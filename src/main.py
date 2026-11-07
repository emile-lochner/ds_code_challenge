import data
import validation
import json
import h3
import sqlite3
import pandas as pd
import time
import requests
import os
from shapely.geometry import Polygon
import datetime

# This is to control which parts of the pipeline to run
do_task_1 = False
do_task_2 = False
rebuild_task_2_db = False
do_task_5 = True
download_wind_data = False
rebuild_wind_data_db = True

# Constants that control parts of the pipeline
H3_RESOLUTION = 8
H3_LIMIT = 10
SERVICE_REQUESTS_FPATH = "data/sr.csv"
SERVICE_REQUESTS_WITH_H3_FPATH = "data/sr_hex.csv"
OUTPUT_DB = "data/service_requests.db"

# ---------------------------------------------
# Task 1: Data Extraction
# ---------------------------------------------
if do_task_1:
    h3_cells_aws = data.get_h3_cells_from_aws(H3_RESOLUTION, H3_LIMIT)
    h3_cells_file = data.get_h3_cells_from_file("data/city-hex-polygons-8.geojson", H3_LIMIT)

    h3_cells_all = {}

    def add_cell(cell:dict, source:str, data_dict: dict):
        idx = data.get_cell_index(cell)

        if idx not in data_dict:
            # Initialise the dictionary
            data_dict[idx] = {
                "aws": {
                    "is_valid": False,
                    "centroid": None,
                    "vertices": None
                },
                "file": {
                    "is_valid": False,
                    "centroid": None,
                    "vertices": None
                }
            }

        is_valid = validation.h3_validation(cell, H3_RESOLUTION)
        if is_valid:
            data_dict[idx][source]["centroid"] = data.get_cell_centroid(cell)
            data_dict[idx][source]["vertices"] = data.get_cell_vertices(cell)
            data_dict[idx][source]["is_valid"] = True

    for cell in h3_cells_aws:
        add_cell(cell, "aws", h3_cells_all)

    for cell in h3_cells_file:
        add_cell(cell, "file", h3_cells_all)

    # Check conformity between the file and the aws sources for each cell index
    n_file_ok = 0
    n_file_err = 0

    n_aws_ok = 0
    n_aws_err = 0

    for idx, sub_dict in h3_cells_all.items():
        if sub_dict["aws"]["is_valid"]:
            n_aws_ok += 1
        else:
            n_aws_err += 1

        if sub_dict["file"]["is_valid"]:
            n_file_ok += 1
        else:
            n_file_err += 1

        if sub_dict["aws"]["vertices"] != sub_dict["file"]["vertices"]:
            print("Vertex error")

# ---------------------------------------------
# Task 2: Initial Data Transformation
# ---------------------------------------------
if do_task_2:
    # Used for timing analysis
    tic_start = time.perf_counter()

    if rebuild_task_2_db:
        # Build the table from the raw service requests data
        df = pd.read_csv(SERVICE_REQUESTS_FPATH, index_col=0)
        df.index.name = "id"

        with sqlite3.connect(OUTPUT_DB) as con:
            df.to_sql("requests", con, if_exists="replace", index=False)
            con.execute("ALTER TABLE requests ADD COLUMN h3_level8_index TEXT DEFAULT '0'")
            con.execute("ALTER TABLE requests ADD COLUMN creation_timestamp_unix INTEGER DEFAULT '0'")
            con.execute("CREATE INDEX IF NOT EXISTS idx_notification ON requests(notification_number)")

            query_timestamp_unix = '''
                UPDATE requests
                SET creation_timestamp_unix = CAST(strftime('%s', src.creation_timestamp) AS INTEGER) 
                FROM requests AS src
                WHERE src.notification_number = requests.notification_number;
            '''
            con.execute(query_timestamp_unix)

            con.commit()

        # Build the table from the verification CSV file. This will be used to check our work.
        df = pd.read_csv(SERVICE_REQUESTS_WITH_H3_FPATH, usecols=["notification_number", "h3_level8_index"])
        with sqlite3.connect(OUTPUT_DB) as con:
            df.to_sql("h3_validation", con, if_exists="replace", index=False)
            con.execute("CREATE INDEX IF NOT EXISTS idx_notification ON requests(notification_number)")
            con.commit()

    with sqlite3.connect(OUTPUT_DB) as con:
        # Get all the gps coordinates and find their corresponding level8_index
        cur_fetch = con.cursor()
        cur_update = con.cursor()

        fetch_query = '''
            SELECT 
                notification_number,
                latitude,
                longitude
            FROM requests 
            WHERE 
                latitude IS NOT NULL 
                and longitude IS NOT NULL
                and h3_level8_index == '0';
        '''

        quantity_query = '''
            SELECT count(*)
            FROM requests
            WHERE 
                latitude IS NOT NULL 
                and longitude IS NOT NULL
                and h3_level8_index == '0';
        '''

        no_index_query = '''
            SELECT count(*)
            FROM requests
            WHERE 
                h3_level8_index == '0';
        '''

        update_query = '''
            UPDATE requests
            SET h3_level8_index = ?
            WHERE notification_number = ?;
        '''

        # Get the number of rows that needs to be updated, this is useful for progress logging
        cur_fetch.execute(quantity_query)
        row = cur_fetch.fetchone()
        N_rows = row[0]

        cur_fetch.execute(fetch_query)
        n_done = 0

        while True:
            row = cur_fetch.fetchone()
            if row is None:
                break

            notification = row[0]
            lat = row[1]
            lon = row[2]
            cell_index = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

            cur_update.execute(update_query, (cell_index, notification))

            n_done += 1
            if n_done % 100 == 0:
                print(f"Progress: {n_done} / {N_rows}")

        con.commit()

        # Validate that all the h3_level8_indices are correct based on the validation file.
        validation_query = '''
            SELECT 
                h3v.notification_number,
                h3v.h3_level8_index as h3_validation,
                req.h3_level8_index as h3_requests
            FROM h3_validation AS h3v
            INNER JOIN requests AS req ON req.notification_number = h3v.notification_number
            WHERE req.h3_level8_index != h3v.h3_level8_index;
        '''

        cur_fetch.execute(validation_query)
        rows = cur_fetch.fetchall()

        if len(rows) == 0:
            print("All h3_level8_index values match reference file.")

        else:
            print("The following notification_numbers have errors in their h3_level8_index values:")
            for row in rows:
                print(f"notification: {row[0]} validation_index: {row[1]} generated_index: {row[2]}")

        # Display how many rows could not be assigned a h3_level8_cell
        cur_fetch.execute(no_index_query)
        rows = cur_fetch.fetchone()

        print(f"{rows[0]} rows could not be assigned a h3_level8_index.")

    # Timing analysis
    dt = time.perf_counter() - tic_start
    print(f"Task 2 took {dt:.1f} seconds to complete")

# ---------------------------------------------
# Task 5: Further Data Transformations
# ---------------------------------------------
if do_task_5:
    if download_wind_data:
        data.get_wind_data()

    if rebuild_wind_data_db:
        # Build the table from the wind data xlsx file
        df = pd.read_excel("data/wind.xlsx", skiprows=2, header=[0, 1, 2], skipfooter=8) 

        # Flatten the 3 levels into one name, dropping empty "Unnamed: ..." parts and replacing some problematic characters
        df.columns = [
            "_".join(str(p).strip() for p in col if not str(p).startswith("Unnamed")).replace(" ", "_").replace("/", "p").replace("&", "").replace("__", "").lower()
            for col in df.columns
        ]

        dt = pd.to_datetime(df["datetime"], format="%d/%m/%Y %H:%M").dt.tz_localize("Africa/Johannesburg")
        df["timestamp_unix"] = dt.map(pd.Timestamp.timestamp).astype(int)

        with sqlite3.connect(OUTPUT_DB) as con:
            df.to_sql("wind", con, if_exists="replace", index=False)
            #con.execute("ALTER TABLE wind ADD COLUMN timestamp_unix INTEGER DEFAULT '0'")


    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": "Atlantis, Cape Town, South Africa",
            "format": "jsonv2",
            "polygon_geojson": 1,
            "limit": 5,
        },
        headers={"User-Agent": f"coct_ds_challenge/1.0 {os.environ['OPENMAP_USERNAME']}"},
        timeout=30,
    )
    r.raise_for_status()

    # for place in r.json():
    #     print(place["display_name"], place["type"], place["geojson"]["type"])

    geom = r.json()[0]["geojson"]  # GeoJSON Polygon or MultiPolygon
    outline_coords = geom["coordinates"]   # [lon, lat] pairs

    # Convert from the GeoJSON format to a list of tuples required by shapely
    outline_sequence = []
    for coords in outline_coords[0]:
        outline_sequence.append(tuple(coords))

    centroid_point = Polygon(outline_sequence).centroid
    # centroid_point.x = longitude
    # centroid_point.y = latitude
    # print(centroid_point)

    # Create the requests subset within 1 arcminute of this centroid
    with sqlite3.connect(OUTPUT_DB) as con:
        cur = con.cursor()

        query_delete_table = '''
            DROP TABLE IF EXISTS atlantis_requests;
        '''
        cur.execute(query_delete_table)
        con.commit()

        query_create_table = '''
            CREATE TABLE atlantis_requests (
                notification_number INTEGER PRIMARY KEY,
                creation_timestamp_unix INTEGER,
                wind_speed_mps REAL,
                wind_direction_deg REAL
            )
        '''
        cur.execute(query_create_table)
        con.commit()

        query_insert_data = '''
            INSERT INTO atlantis_requests (notification_number, creation_timestamp_unix)
            SELECT notification_number, creation_timestamp_unix
            FROM requests
            WHERE pow(latitude - ?, 2) + pow(longitude - ?, 2) <= pow(?, 2)
        '''
        cur.execute(query_insert_data, (centroid_point.y, centroid_point.x, 1.0/60.0))
        con.commit()

        # Get the closest wind data for each record in the Atlantis requests subset
        query_fetch = '''
            SELECT 
                notification_number,
                creation_timestamp_unix
            FROM atlantis_requests;
        '''
        cur.execute(query_fetch)
        for row in cur.fetchall():
            notification = row[0]
            ts = row[1]

            query_wind = '''
                SELECT atlantis_aqm_site_wind_speed_v_mps, atlantis_aqm_site_wind_dir_v_deg, abs(wind.timestamp_unix - ?) as dt
                FROM wind
                WHERE dt <= 3600.0
                ORDER BY dt ASC
            '''
            cur.execute(query_wind, (int(ts),))
            wind_rows = cur.fetchall()

            if wind_rows:
                for wind_data in wind_rows:
                    try:
                        #print(wind_data)
                        wind_speed = float(wind_data[0])
                        wind_dir = float(wind_data[1])

                        query_update = '''
                            UPDATE atlantis_requests
                            SET
                                wind_speed_mps = ?,
                                wind_direction_deg = ?
                            WHERE 
                                notification_number = ?;
                        '''
                        cur.execute(query_update, (wind_speed, wind_dir, notification))
                        break

                    except Exception as e:
                        print(f"Could not update atlantis_request wind data: {e}")
                
            else:
                print("No wind data for this timestep.")

        con.commit()
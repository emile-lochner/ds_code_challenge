import os
import requests
import time
import pandas as pd
import sqlite3
from shapely.geometry import Polygon
from tqdm import tqdm

def get_wind_data():
    """Download the wind data spreadsheet, resuming partial downloads, with up to 10 attempts."""

    print(" - Fetching wind speed and direction data.")
    tic_start = time.perf_counter()
    
    url = "https://www.arcgis.com/sharing/rest/content/items/31ef242a23484e79bbb19d6b29203179/data"
    out = "data/wind.xlsx"
    os.makedirs("data", exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(1, 11):
        pos = os.path.getsize(out) if os.path.exists(out) else 0
        h = dict(headers, **({"Range": f"bytes={pos}-"} if pos else {}))
        try:
            with requests.get(url, headers=h, stream=True, timeout=(10, 60)) as r:
                if r.status_code == 416:  # already complete
                    break
                r.raise_for_status()
                if pos and r.status_code != 206:  # server ignored Range, restart
                    pos = 0
                with open(out, "ab" if pos else "wb") as f:
                    for chunk in r.iter_content(1024 * 1024):
                        f.write(chunk)
            break
        except requests.RequestException as e:
            print(f"Attempt {attempt} failed: {e}")
            time.sleep(5)
    else:
        raise SystemExit("Download failed")

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def build_database_from_wind_xlsx():
    """Read the wind spreadsheet, clean the column names, add a unix timestamp and store it in the `wind` table."""

    print(" - Building wind data table from spreadsheet.")
    tic_start = time.perf_counter()
    
    # Build the table from the wind data xlsx file
    df = pd.read_excel("data/wind.xlsx", skiprows=2, header=[0, 1, 2], skipfooter=8) 

    # Flatten the 3 levels into one name, dropping empty "Unnamed: ..." parts and replacing some problematic characters
    df.columns = [
        "_".join(str(p).strip() for p in col if not str(p).startswith("Unnamed")).replace(" ", "_").replace("/", "p").replace("&", "").replace("__", "").lower()
        for col in df.columns
    ]

    # Add a unix timestamp column. This makes some of the further analysis much simpler.
    dt = pd.to_datetime(df["datetime"], format="%d/%m/%Y %H:%M").dt.tz_localize("Africa/Johannesburg")
    df["timestamp_unix"] = dt.map(pd.Timestamp.timestamp).astype(int)

    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        df.to_sql("wind", con, if_exists="replace", index=False)

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def get_suburb_centroid_coords(suburb: str) -> dict:
    """Look up a suburb's outline via OpenStreetMap and compute its centroid.

    Parameters
    ----------
    suburb : str
        Name of the suburb to search for.

    Returns
    -------
    dict
        Centroid coordinates with keys "lat" and "lon".
    """

    print(f" - Get centroid coordinates for \'{suburb}\'")
    tic_start = time.perf_counter()
    
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": suburb,
            "format": "jsonv2",
            "polygon_geojson": 1,
            "limit": 5,
        },
        headers={"User-Agent": f"coct_ds_challenge/1.0 {os.environ['OPENMAP_USERNAME']}"},
        timeout=30,
    )
    r.raise_for_status()

    geom = r.json()[0]["geojson"]  # GeoJSON Polygon or MultiPolygon
    outline_coords = geom["coordinates"]   # [lon, lat] pairs

    # Convert from the GeoJSON format to a list of tuples required by shapely
    outline_sequence = []
    for coords in outline_coords[0]:
        outline_sequence.append(tuple(coords))

    # centroid_point.x = longitude
    # centroid_point.y = latitude
    centroid_point = Polygon(outline_sequence).centroid

    centroid = {
            "lon": centroid_point.x,
            "lat": centroid_point.y
        }

    print(f"coordinates obtained for \'{suburb}\':")
    print(f"Latitude: {centroid['lat']}")
    print(f"Longitude: {centroid['lon']}")

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

    return centroid

def create_requests_subset_for_wind_data(centroid_point: dict, arcminute_radius: float):
    """Create the `requests_subset` table with requests within a radius of a centroid.

    Parameters
    ----------
    centroid_point : dict
        Centre point with keys "lat" and "lon".
    arcminute_radius : float
        Search radius in arcminutes.
    """

    print(f" - Create service requests subset table for wind data.")
    tic_start = time.perf_counter()
    
    # Create the requests subset within 1 arcminute of this centroid
    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        cur = con.cursor()

        query_delete_table = '''
            DROP TABLE IF EXISTS requests_subset;
        '''
        cur.execute(query_delete_table)
        con.commit()

        query_create_table = '''
            CREATE TABLE requests_subset (
                notification_number INTEGER PRIMARY KEY,
                creation_timestamp_unix INTEGER,
                wind_speed_mps REAL,
                wind_direction_deg REAL
            )
        '''
        cur.execute(query_create_table)
        con.commit()

        query_insert_data = '''
            INSERT INTO requests_subset (notification_number, creation_timestamp_unix)
            SELECT notification_number, creation_timestamp_unix
            FROM requests
            WHERE pow(latitude - ?, 2) + pow(longitude - ?, 2) <= pow(?, 2)
        '''
        cur.execute(query_insert_data, (centroid_point["lat"], centroid_point["lon"], arcminute_radius/60.0))
        con.commit()

        query_created = '''
            SELECT count(*)
            FROM requests_subset;
        '''
        cur.execute(query_created)
        rows = cur.fetchone()
        print(f"Subset table contains {rows[0]} rows.")

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def add_wind_data_to_subset():
    """Add the wind speed and direction closest in time (within 1 hour) to each request in `requests_subset`."""

    print(f" - Populate requests subset with wind data.")
    tic_start = time.perf_counter()
    
    # Get the closest wind data for each record in the Atlantis requests subset
    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        cur = con.cursor()

        query_fetch = '''
            SELECT 
                notification_number,
                creation_timestamp_unix
            FROM requests_subset;
        '''
        cur.execute(query_fetch)
        rows = cur.fetchall()
        for idx in tqdm(range(len(rows)), desc="Progress"):
            row = rows[idx]
            notification = row[0]
            ts = row[1]

            # Select closest data within 1 hour of request time
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
                        wind_speed = float(wind_data[0])
                        wind_dir = float(wind_data[1])
                    except:
                        # Wind data not valid
                        continue

                    query_update = '''
                        UPDATE requests_subset
                        SET
                            wind_speed_mps = ?,
                            wind_direction_deg = ?
                        WHERE 
                            notification_number = ?;
                    '''
                    cur.execute(query_update, (wind_speed, wind_dir, notification))
                    break
                    
            con.commit()

        # Check how many rows we updated
        query_count_all = '''
            SELECT count(*)
            FROM requests_subset;
        '''
        cur.execute(query_count_all)
        rows = cur.fetchone()
        total_count = rows[0]
        
        query_count_success = '''
            SELECT count(*)
            FROM requests_subset
            WHERE wind_speed_mps IS NOT NULL 
            AND wind_direction_deg IS NOT NULL;
        '''
        cur.execute(query_count_success)
        rows = cur.fetchone()
        success_count = rows[0]

        print(f"{success_count} / {total_count} [{(success_count / total_count) * 100:.1f}%] successfully updated")

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def anonymise_augmented_subsample_data():
    """Create the `anonymous_requests` table with timestamps rounded to 6-hour intervals and identifying columns removed."""

    print(f" - Anonymise augmented subsample data.")
    tic_start = time.perf_counter()

    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        cur = con.cursor()
        
        # Delete the old table if it exists
        query_delete_table = '''
            DROP TABLE IF EXISTS anonymous_requests;
        '''
        cur.execute(query_delete_table)
        con.commit()

        # Create anonymised subset table
        query_create_table = '''
            CREATE TABLE anonymous_requests (
                creation_timestamp_approx TEXT,
                completion_timestamp_approx TEXT,
                h3_level8_index TEXT,
                directorate TEXT,
                department TEXT,
                branch TEXT,
                section TEXT,
                code_group TEXT,
                code TEXT,
                cause_code_group TEXT,
                cause_code TEXT,
                official_suburb TEXT,
                wind_speed_mps REAL,
                wind_direction_deg REAL
            );
        '''
        cur.execute(query_create_table)
        con.commit()

        # Add data
        query_insert = '''
            INSERT INTO anonymous_requests (
                creation_timestamp_approx,
                completion_timestamp_approx,
                h3_level8_index,
                directorate,
                department,
                branch,
                section,
                code_group,
                code,
                cause_code_group,
                cause_code,
                official_suburb,
                wind_speed_mps,
                wind_direction_deg
            )
            SELECT 
                strftime(
                        '%Y-%m-%d %H:%M:%S',
                        CAST(ROUND((CAST(strftime('%s', substr(req.creation_timestamp, 1, 19)) AS INTEGER) - 10800) / 21600.0) * 21600 + 10800 AS INTEGER),
                        'unixepoch'
                    ) || substr(req.creation_timestamp, 20) as creation_timestamp_approx,
                strftime(
                        '%Y-%m-%d %H:%M:%S',
                        CAST(ROUND((CAST(strftime('%s', substr(req.completion_timestamp, 1, 19)) AS INTEGER) - 10800) / 21600.0) * 21600 + 10800 AS INTEGER),
                        'unixepoch'
                    ) || substr(req.completion_timestamp, 20) as completion_timestamp_approx,
                req.h3_level8_index,
                req.directorate,
                req.department,
                req.branch,
                req.section,
                req.code_group,
                req.code,
                req.cause_code_group,
                req.cause_code,
                req.official_suburb,
                subs.wind_speed_mps,
                subs.wind_direction_deg
            FROM requests AS req
            INNER JOIN requests_subset AS subs ON req.notification_number = subs.notification_number;
        '''

        cur.execute(query_insert)
        con.commit()

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def export_anonymous_csv_file():
    """Export the `anonymous_requests` table to `export/anonymous.csv`."""
    
    print(" - Export anonymous CSV file.")
    tic_start = time.perf_counter()

    os.makedirs("export", exist_ok=True)

    f_out = open("export/anonymous.csv", 'w')
    header = [
        "creation_timestamp_approx",
        "completion_timestamp_approx",
        "h3_level8_index",
        "directorate",
        "department",
        "branch",
        "section",
        "code_group",
        "code",
        "cause_code_group",
        "cause_code",
        "official_suburb",
        "wind_speed_mps",
        "wind_direction_deg"
        ]
    f_out.write(",".join(header) + "\n")

    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        cur = con.cursor()

        query_fetch = '''
            SELECT
                creation_timestamp_approx,
                completion_timestamp_approx,
                h3_level8_index,
                directorate,
                department,
                branch,
                section,
                code_group,
                code,
                cause_code_group,
                cause_code,
                official_suburb,
                wind_speed_mps,
                wind_direction_deg
            FROM
                anonymous_requests;
        '''

        cur.execute(query_fetch)
        while True:
            row = cur.fetchone()
            if row == None:
                break

            line = ",".join("" if v is None else '"' + str(v) + '"' for v in row)
            f_out.write(line + "\n")

    f_out.close()

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")
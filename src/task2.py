import os
import sqlite3
import pandas as pd
import time
from scipy.spatial import KDTree
from tqdm import tqdm
import numpy as np

def create_service_requests_table():
    print(" - Building requests SQLite table from file.")
    tic_start = time.perf_counter()

    df = pd.read_csv(os.environ["SERVICE_REQUESTS_FPATH"], index_col=0)
    df.index.name = "id"

    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        df.to_sql("requests", con, if_exists="replace", index=False)
        con.execute("ALTER TABLE requests ADD COLUMN h3_level8_index TEXT DEFAULT '0'")
        con.execute("ALTER TABLE requests ADD COLUMN creation_timestamp_unix INTEGER DEFAULT '0'")
        con.execute("CREATE INDEX IF NOT EXISTS idx_notification ON requests(notification_number)")

        # The unix timestamp will be used in Task 5.
        query_timestamp_unix = '''
            UPDATE requests
            SET creation_timestamp_unix = CAST(strftime('%s', src.creation_timestamp) AS INTEGER) 
            FROM requests AS src
            WHERE src.notification_number = requests.notification_number;
        '''
        con.execute(query_timestamp_unix)

        con.commit()

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def create_service_requests_validation_table():
    print(" - Building h3_level8_index validation SQLite table from file.")
    tic_start = time.perf_counter()

    df = pd.read_csv(os.environ["SERVICE_REQUESTS_WITH_H3_FPATH"], usecols=["notification_number", "h3_level8_index"])
    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        df.to_sql("h3_validation", con, if_exists="replace", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS idx_notification ON requests(notification_number)")
        con.commit()

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def join_service_requests_with_h3_cells(h3_cells_polygons: dict):
    print(" - Join the service requests GPS coordinates with a H3 cell reference.")
    tic_start = time.perf_counter()

    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        # Get all the gps coordinates and find their corresponding level8_index
        cur_fetch = con.cursor()
        cur_update = con.cursor()

        # Get the GPS coordinates of the cells
        query_centroids = '''
            SELECT cell_index, centroid_lat, centroid_lon
            FROM h3_cells;
        '''
        cur_fetch.execute(query_centroids)
        centroid_rows = cur_fetch.fetchall()

        # Build the KD Tree
        # This speeds up finding the nearest cells to the request coordinates significantly.
        kd_coords = []
        for cell in centroid_rows:
            lat = cell[1]
            lon = cell[2]

            kd_coords.append((lat, lon))

        cell_tree = KDTree(np.array(kd_coords))

        query_get_requests = '''
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

        # Get the number of rows that needs to be updated, this is useful for progress logging
        query_quantity = '''
            SELECT count(*)
            FROM requests
            WHERE 
                latitude IS NOT NULL 
                and longitude IS NOT NULL
                and h3_level8_index == '0';
        '''
        cur_fetch.execute(query_quantity)
        row = cur_fetch.fetchone()
        N_rows = row[0]
        
        cur_fetch.execute(query_get_requests)
        for n in tqdm(range(N_rows), desc="Progress"):
            # Since the number of records is large we fetch one at a time to save on memory requirements.
            row = cur_fetch.fetchone()
            if row is None:
                continue

            notification = row[0]
            lat = row[1]
            lon = row[2]

            d, idx = cell_tree.query(np.array((lat, lon)))

            cell_index = centroid_rows[idx][0]
            if cell_index not in h3_cells_polygons:
                continue

            polygon = h3_cells_polygons[cell_index]
            if polygon.contains(Point(lon, lat)):
                update_query = '''
                    UPDATE requests
                    SET h3_level8_index = ?
                    WHERE notification_number = ?;
                '''
                cur_update.execute(update_query, (cell_index, notification))

        con.commit()

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def validate_h3_indices():
    print(" - Join the service requests GPS coordinates with a H3 cell reference.")
    tic_start = time.perf_counter()

    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        cur = con.cursor()

        # Validate that all the h3_level8_indices are correct based on the validation file.
        validation_query = '''
            SELECT count(*)
            FROM h3_validation AS h3v
            INNER JOIN requests AS req ON req.notification_number = h3v.notification_number
            WHERE req.h3_level8_index != h3v.h3_level8_index
            AND req.h3_level8_index != '0';
        '''

        cur.execute(validation_query)
        rows = cur.fetchone()
        print(f"{rows[0]} records have been assigned an incorrect h3_level8_index.")

        # Display how many rows could not be assigned a h3_level8_cell
        no_index_query = '''
            SELECT count(*)
            FROM requests
            WHERE 
                h3_level8_index == '0';
        '''

        cur.execute(no_index_query)
        rows = cur.fetchone()
        print(f"{rows[0]} records could not be assigned a h3_level8_index.")

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")
# import data
# import validation
# import json
# import h3
# import sqlite3
# import pandas as pd
# import time
# import requests
# import os
# from shapely.geometry import Polygon
# import datetime

import time
import sqlite3

import data
import validation

# This is to control which parts of the pipeline to run
pipeline_control = {
    "task1": {
    },
    "task2": {},
    "task5": {}
}

# do_task_1 = False
# do_task_2 = False
# rebuild_task_2_db = False
# do_task_5 = True
# download_wind_data = False
# rebuild_wind_data_db = True

# Constants that control parts of the pipeline
H3_RESOLUTION = 8
H3_LIMIT = -1
SERVICE_REQUESTS_FPATH = "data/sr.csv"
SERVICE_REQUESTS_WITH_H3_FPATH = "data/sr_hex.csv"
OUTPUT_DB = "data/database.db"

print("-"*60)
print("CoCT Data Engineering Challenge")
print("-"*60)
# ---------------------------------------------
# Task 1: Data Extraction
# ---------------------------------------------
print("Task 1: Data Extraction")
print("-"*60)
tic_start = time.perf_counter()

# Read in data from AWS and from the supplied validation file
h3_cells_aws = data.get_h3_cells_from_aws(H3_RESOLUTION, H3_LIMIT)
h3_cells_file = data.get_h3_cells_from_file("data/city-hex-polygons-8.geojson", H3_LIMIT)

# Validate using city-hex-polygons-8.geojson supplied
h3_cells_valid = validation.h3_validation(h3_cells_aws, h3_cells_file, H3_RESOLUTION)

# Build a sqlite database to store the valid cell data
with sqlite3.connect(OUTPUT_DB) as con:
    print("\n - Storing valid cells in SQLite database.")
    cur = con.cursor()

    # Delete the old table if it exists
    query_delete_table = '''
        DROP TABLE IF EXISTS h3_cells;
    '''
    cur.execute(query_delete_table)
    con.commit()

    query_create_table = '''
        CREATE TABLE h3_cells (
            cell_index TEXT PRIMARY KEY,
            centroid_lat REAL,
            centroid_lon REAL,
            polygon TEXT
        );
    '''
    cur.execute(query_create_table)
    con.commit()

    query_insert = '''
        INSERT INTO h3_cells (cell_index, centroid_lat, centroid_lon, polygon)
        VALUES (?,?,?,?);
    '''
    for cell in h3_cells_valid:
        index = data.get_cell_index(cell)
        centroid = data.get_cell_centroid(cell)
        polygon = data.get_cell_vertices(cell)

        cur.execute(query_insert, (index, centroid["lat"], centroid["lon"], str(polygon)))
    con.commit()

tic_end = time.perf_counter()
dt = tic_end - tic_start
print(f"\nTime taken for Task 1: {dt:.1f} seconds.")

# ---------------------------------------------
# Task 2: Initial Data Transformation
# ---------------------------------------------
print("\nTask 2: Initial Data Transformation")
print("-"*60)
tic_start = time.perf_counter()

tic_end = time.perf_counter()
dt = tic_end - tic_start
print(f"\nTime taken for Task 2: {dt:.1f} seconds.")
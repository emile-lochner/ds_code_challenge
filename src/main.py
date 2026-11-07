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
OUTPUT_DB = "data/service_requests.db"

# ---------------------------------------------
# Task 1: Data Extraction
# ---------------------------------------------
tic_start = time.perf_counter()

# Read in data from AWS and from the supplied validation file
h3_cells_aws = data.get_h3_cells_from_aws(H3_RESOLUTION, H3_LIMIT)
h3_cells_file = data.get_h3_cells_from_file("data/city-hex-polygons-8.geojson", H3_LIMIT)

# Validate using city-hex-polygons-8.geojson supplied
h3_cells_valid = validation.h3_validation(h3_cells_aws, h3_cells_file, H3_RESOLUTION)

# Check validation of data with conformance score
# Log Time to perform validation steps

tic_end = time.perf_counter()
dt = tic_end - tic_start
print(f"\nTime taken for Task 1: {dt:.1f} seconds.")
import data
import validation
import json
import h3
import sqlite3
import pandas as pd

# ---------------------------------------------
# Task 1: Data Extraction
# ---------------------------------------------
H3_RESOLUTION = 8
H3_LIMIT = 10

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
SERVICE_REQUESTS_FPATH = "data/sr.csv"
OUTPUT_DB = "data/service_requests.db"

# con = sqlite3.connect(OUTPUT_DB)

df = pd.read_csv(SERVICE_REQUESTS_FPATH, index_col=0)
df.index.name = "id"

with sqlite3.connect(OUTPUT_DB) as con:
    df.to_sql("requests", con, if_exists="replace", index=False)
    con.execute("ALTER TABLE requests ADD COLUMN h3_level8_index TEXT DEFAULT '0'")
    con.execute("CREATE INDEX IF NOT EXISTS idx_notification ON requests(notification_number)")
    con.commit()

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
            and longitude IS NOT NULL;
    '''

    quantity_query = '''
        SELECT count(*)
        FROM requests
        WHERE 
            latitude IS NOT NULL 
            and longitude IS NOT NULL;
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


# header_to_idx = {}
# first_line = True
# debug_limit = 10

# with open(SERVICE_REQUESTS_FPATH, 'r') as file:
#     for line in file:
#         line = line.strip()
#         words = line.split(',')

#         if first_line:
#             idx = 0
#             for word in words:
#                 header_to_idx[word] = idx
#                 idx += 1
#             first_line = False

#             # Create the database table
#             sql = '''
#                 CREATE TABLE IF NOT EXISTS requests 
#             '''

#             continue

#         cell_index = 0
#         try:
#             coords = {
#                 "lat": float(words[header_to_idx["latitude"]]),
#                 "lon": float(words[header_to_idx["longitude"]])
#             }
#             cell_index = h3.latlng_to_cell(coords["lat"], coords["lon"], H3_RESOLUTION)

#         except:
#             print("No Coordinates")

        

#         if debug_limit > 0:
#             debug_limit -= 1
#             if debug_limit == 0:
#                 break

# output.close()
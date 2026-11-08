import time
import json
import boto3
import os
import sqlite3

import data

def get_h3_cells_from_file(fpath: str, limit = -1):
    print(" - Compiling H3 data from reference file.")
    tic_start = time.perf_counter()

    cell_list = []
    with open(fpath, 'r') as fp:
        data = json.load(fp)

        for cell in data["features"]:
            cell_list.append(cell)

            if limit > 0:
                limit -= 1
                if limit == 0:
                    break

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Obtained {len(cell_list)} records.")
    print(f"Done: {dt:.1f} seconds.")

    return cell_list

def get_h3_cells_from_aws(resolution: int, limit = -1):
    print(" - Fetching and compiling H3 data from AWS.")
    tic_start = time.perf_counter()

    cell_list = []

    # Get data from AWS
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"]
        )

    r = int(resolution)

    if limit < 0:
        query = f'''SELECT * FROM S3Object[*].features[*] f WHERE f.properties.resolution = {r}'''
    else:
        query = f'''SELECT * FROM S3Object[*].features[*] f WHERE f.properties.resolution = {r} LIMIT {limit}'''

    response = s3.select_object_content(
        Bucket="cct-ds-code-challenge-input-data",
        Key="city-hex-polygons-8-10.geojson",
        ExpressionType="SQL",
        Expression=query,
        InputSerialization={"JSON": {"Type": "DOCUMENT"}},
        OutputSerialization={"JSON": {}},
    )

    buffer = ""
    for event in response["Payload"]:
        if "Records" in event:
            buffer += event["Records"]["Payload"].decode("utf-8")
            *lines, buffer = buffer.split("\n")
            for line in lines:
                row = json.loads(line)  # one row as a dict
                cell_list.append(row)

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Obtained {len(cell_list)} records.")
    print(f"Done: {dt:.1f} seconds.")

    return cell_list

def create_h3_cells_table():
    print(" - Create h3_cells table in database.")
    tic_start = time.perf_counter()

    # Build a sqlite database to store the valid cell data
    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
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

    cur.close()

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

def save_h3_cells_to_db(cells:list):
    print(" - Storing valid h3_cells in database.")
    tic_start = time.perf_counter()

    with sqlite3.connect(os.environ["OUTPUT_DB"]) as con:
        cur = con.cursor()
        query_insert = '''
            INSERT INTO h3_cells (cell_index, centroid_lat, centroid_lon, polygon)
            VALUES (?,?,?,?);
        '''
        for cell in cells:
            index = data.get_cell_index(cell)
            centroid = data.get_cell_centroid(cell)
            polygon = data.get_cell_vertices(cell)
    
            cur.execute(query_insert, (index, centroid["lat"], centroid["lon"], str(polygon)))
        con.commit()

    cur = con.cursor()

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")

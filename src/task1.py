import time
import json
import boto3
import os
import sqlite3

import data

def get_h3_cells_from_file(fpath: str):
    """Load H3 cell features from a local GeoJSON file.

    Parameters
    ----------
    fpath : str
        Path to the GeoJSON file.

    Returns
    -------
    list
        H3 cell features.
    """

    print(" - Compiling H3 data from reference file.")
    tic_start = time.perf_counter()

    cell_list = []
    with open(fpath, 'r') as fp:
        file_data = json.load(fp)

        for cell in file_data["features"]:
            cell_list.append(cell)

    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Obtained {len(cell_list)} records.")
    print(f"Done: {dt:.1f} seconds.")

    return cell_list

def get_h3_cells_from_aws(resolution: int):
    """Fetch H3 cell features of a given resolution from S3 using S3 Select.

    Parameters
    ----------
    resolution : int
        H3 resolution to select.

    Returns
    -------
    list
        H3 cell features.
    """

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

    query = f'''SELECT * FROM S3Object[*].features[*] f WHERE f.properties.resolution = {r}'''

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
    """Create an empty `h3_cells` table in the database, replacing any existing one."""

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
    """Insert H3 cells into the `h3_cells` table.

    Parameters
    ----------
    cells : list
        Valid H3 cell features to store.
    """

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

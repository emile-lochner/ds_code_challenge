import boto3
import h3
from dotenv import load_dotenv
import os
import json

# Load environment variables from the .env file in the root directory
load_dotenv()

def get_cell_index(cell: dict):
    return cell["properties"]["index"]

def get_cell_centroid(cell: dict):
    centroid = {
        "lat": cell["properties"]["centroid_lat"],
        "lon": cell["properties"]["centroid_lon"]
    }
    return centroid

def get_cell_vertices(cell: dict):
    return cell["geometry"]["coordinates"]

def get_h3_cells_from_file(fpath: str, limit = -1):
    cell_list = []
    with open(fpath, 'r') as fp:
        data = json.load(fp)

        for cell in data["features"]:
            cell_list.append(cell)

            if limit > 0:
                limit -= 1
                if limit == 0:
                    return cell_list

    return cell_list

def get_h3_cells_from_aws(resolution: int, limit = -1):
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

    return cell_list

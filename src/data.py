import boto3
import h3
from dotenv import load_dotenv
import os
import requests
import json
import time

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
    print("\n - Compiling H3 data from reference file.")
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
    print("\n - Fetching and compiling H3 data from AWS.")
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

def get_wind_data():
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
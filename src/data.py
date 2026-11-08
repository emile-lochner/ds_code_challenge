import os
import requests
from shapely.geometry import Polygon
import gzip
import shutil

def geojson_to_polygon(geojson: list) -> Polygon:
    cell_tuples = []
    for coord in geojson[0]:
        cell_tuples.append(tuple(coord))

    cell_poly = Polygon(cell_tuples)
    return cell_poly

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


def download_data_files():
    print(" - Downloading required data files.")
    os.makedirs("data", exist_ok=True)

    # Get the hex polygons file
    url = "https://cct-ds-code-challenge-input-data.s3.af-south-1.amazonaws.com/city-hex-polygons-8.geojson"
    out = os.path.join("data", os.path.basename(url))

    if os.path.isfile(out):
        print(f"Already have {os.path.basename(url)}, skipping.")

    else:
        print(f"Fetching {os.path.basename(url)}")
        with requests.get(url, stream=True, timeout=(10, 60)) as r:  # follows redirects like -L
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
        print("Done.")

    # Get the service request file
    url = "https://cct-ds-code-challenge-input-data.s3.af-south-1.amazonaws.com/sr.csv.gz"
    out = os.path.join("data", os.path.basename(url))

    if os.path.isfile(out):
        print(f"Already have {os.path.basename(url)}, skipping.")

    else:
        print(f"Fetching {os.path.basename(url)}")
        with requests.get(url, stream=True, timeout=(10, 60)) as r:  # follows redirects like -L
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)

        shutil.copyfileobj(gzip.open('data/sr.csv.gz'), open('data/sr.csv','wb'))
        print("Done.")
    
    # Get the service request validation file
    url = "https://cct-ds-code-challenge-input-data.s3.af-south-1.amazonaws.com/sr_hex.csv.gz"
    out = os.path.join("data", os.path.basename(url))

    if os.path.isfile(out):
        print(f"Already have {os.path.basename(url)}, skipping.")
    else:
        print(f"Fetching {os.path.basename(url)}")
        with requests.get(url, stream=True, timeout=(10, 60)) as r:  # follows redirects like -L
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)

        shutil.copyfileobj(gzip.open('data/sr_hex.csv.gz'), open('data/sr_hex.csv','wb'))
        print("Done.")
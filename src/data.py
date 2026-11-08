import os
import requests
import time
from shapely.geometry import Polygon

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
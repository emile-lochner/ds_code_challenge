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



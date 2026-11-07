import h3
import json
import time
import data
from geopy.distance import geodesic
from shapely.geometry import Polygon

def _calculate_polygon_overlap(cell:dict, ref_cell:dict) -> float:
    cell_outline = data.get_cell_vertices(cell)
    ref_outline = data.get_cell_vertices(ref_cell)

    cell_tuples = []
    ref_tuples = []

    for coord in cell_outline[0]:
        cell_tuples.append(tuple(coord))

    for coord in ref_outline[0]:
        ref_tuples.append(tuple(coord))

    cell_poly = Polygon(cell_tuples)
    ref_poly = Polygon(ref_tuples)

    intersection = ref_poly.intersection(cell_poly).area
    return intersection / ref_poly.area

def _calculate_centroid_distance(cell:dict, ref_cell:dict) -> float:
    cell_centroid = data.get_cell_centroid(cell)
    ref_centroid = data.get_cell_centroid(ref_cell)

    cell_tuple = (cell_centroid["lat"], cell_centroid["lon"])
    ref_tuple = (ref_centroid["lat"], ref_centroid["lon"])

    distance = geodesic(cell_tuple, ref_tuple)

    return distance.meters

def _check_h3_structure(cell:dict, h3_resolution: int) -> bool:
    '''
    We expect the cell dictionary to have a specific structure as shown below.
    Of these the most critical for our purpose is the index, centroid coordinates and the geometry.
    This function checks that the cell has all of these. If it does not the cell will get rejected.

    Expected structure:
    {
        "type": "Feature",
        "properties": {
            "index": <STRING>,
            "centroid_lat": <FLOAT>,
            "centroid_lon": <FLOAT>,,
            "resolution": <INT>
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": <LIST OF LISTS>
        }
    }
    '''

    # Check that all the required keywords are present in the cell dictionary.
    if "properties" not in cell:
        print("Invalid: Cell does not contain keyword 'properties'.")
        return False

    if "index" not in cell["properties"]:
        print("Invalid: Cell does not contain keyword 'index'.")
        False

    if "centroid_lat" not in cell["properties"]:
        print("Invalid: Cell does not contain keyword 'properties:centroid_lat'.")
        return False

    if "centroid_lon" not in cell["properties"]:
        print("Invalid: Cell does not contain keyword 'properties:centroid_lon'.")
        return False

    if "geometry" not in cell:
        print("Invalid: Cell does not contain keyword 'geometry'.")
        return False

    if "type" not in cell["geometry"]:
        print("Invalid: Cell does not contain keyword 'geometry:type'.")
        return False

    if "coordinates" not in cell["geometry"]:
        print("Invalid: Cell does not contain keyword 'geometry:coordinates'.")
        return False

    # Validate cell data types
    if isinstance(cell["properties"]["index"], str) == False:
        print("Invalid: cell index is not str.")
        return False

    if isinstance(cell["properties"]["centroid_lat"], float) == False:
        print("Invalid: centroid_lat is not float.")
        return False

    if isinstance(cell["properties"]["centroid_lon"], float) == False:
        print("Invalid: centroid_lon is not float.")
        return False

    if cell["geometry"]["type"] != "Polygon":
        print("Invalid: geometry type is not Polygon.")
        return False

    if isinstance(cell["geometry"]["coordinates"], list) == False:
        print("Invalid: coordinates type is not list.")
        return False   

    # Check coordinates structure
    if len(cell["geometry"]["coordinates"][0]) != 7:
        # Each polygon must be a hexagon with one extra point to close the shape.
        print("Invalid: coordinates list does not have 7 items.")
        return False

    if len(cell["geometry"]["coordinates"][0][0]) != 2:
        # Each coordinate must be a pair.
        print("Invalid: coordinates are not in pairs.")
        return False 

    if cell["geometry"]["coordinates"][0][0] != cell["geometry"]["coordinates"][0][-1]:
        # The first and last coordinate pair must be the same to close the shape.
        print("Invalid: start and end coordinates are not the same.")
        return False

    # Use the h3 package to test that the index is correct for the supplied centroid coordinates
    # Get the index from the cell
    index = cell["properties"]["index"]
    centroid = {
        "lat": cell["properties"]["centroid_lat"],
        "lon": cell["properties"]["centroid_lon"]
    }

    # Check that the index is correct from the centroid coordinates
    if h3.latlng_to_cell(centroid["lat"], centroid["lon"], h3_resolution) != index:
        print("Invalid: Cell index is incorrect.")
        return False

    # Structure of the data is valid
    return True


def _convert_list_to_dict(cell_list:list) -> dict:
    cell_dict = {}
    for cell in cell_list:
        index = data.get_cell_index(cell)
        cell_dict[index] = cell

    return cell_dict

def h3_validation(test_cells:list, reference_cells:list, h3_resolution:int, threshold=0.95,):
    print("\n - Validating H3 data against reference cells")
    tic_start = time.perf_counter()

    valid_cells = []
    reference_dict = _convert_list_to_dict(reference_cells)

    n_accepted = 0
    n_rejected = 0
    n_missing = 0

    for cell in test_cells:
        if _check_h3_structure(cell, h3_resolution) == False:
            # Cell does not have the required structure
            n_rejected += 1
            continue

        index = data.get_cell_index(cell)
        
        if index not in reference_dict:
            # Cell is not contained in the reference cells, hence we cannot do validation
            n_missing += 1
            continue

        ref_cell = reference_dict[index]
        if _check_h3_structure(ref_cell, h3_resolution) == False:
            # Reference cell does not have the correct structure
            n_missing += 1
            continue

        # Test centroid distance
        # GPS systems typically have an accuracy of around 10m, hence for every 10m difference we will reduce the score by 5%
        distance_m = _calculate_centroid_distance(cell, ref_cell)

        score_distance = 1.0 - 0.05 * distance_m / 10.0
        if score_distance < 0.0:
            score_distance = 0.0

        # Test polygon overlap
        overlap_fraction = _calculate_polygon_overlap(cell, ref_cell)

        # Test acceptance threshold
        score = score_distance * overlap_fraction

        if score >= threshold:
            valid_cells.append(cell)
            n_accepted += 1

        else:
            # Cell does not match overlap and position threshold
            n_rejected += 1
            continue

    print(f"Accepted {n_accepted} cells.")
    print(f"Rejected {n_rejected} cells.")
    print(f"Missing {n_missing} cells from validation reference.")


    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")
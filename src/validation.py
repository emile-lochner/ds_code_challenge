import h3
import json
import time
import data

def calculate_polygon_overlap(poly1, poly2) -> float:
    pass

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

def h3_validation(test_cells, reference_cells, threshold=0.95):
    print("\n - Validating H3 data against reference cells")
    tic_start = time.perf_counter()

    valid_cells = []
    reference_dict = _convert_list_to_dict(reference_cells)

    n_accepted = 0
    n_rejected = 0
    n_missing = 0

    for cell in test_cells:
        index = data.get_cell_index(cell)

        if index not in reference_dict:
            # Cell is not contained in the reference cells, hence we cannot do validation
            n_missing += 1
            continue

        


    print(f"Accepted {n_accepted} cells.")
    print(f"Rejected {n_rejected} cells.")
    print(f"Missing {n_missing} cells from validation reference.")


    tic_end = time.perf_counter()
    dt = tic_end - tic_start
    print(f"Done: {dt:.1f} seconds.")
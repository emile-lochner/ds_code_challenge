import h3
import json

def h3_validation(cell: dict, h3_resolution: int):
    '''
    We expect the cell dictionary to have a specific structure. If it does not the cell is invalid and false is returned.
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
    if "type" not in cell:
        return False

    if "properties" not in cell:
        return False

    if "index" not in cell["properties"]:
        False

    if "centroid_lat" not in cell["properties"]:
        return False

    if "centroid_lon" not in cell["properties"]:
        return False

    if "resolution" not in cell["properties"]:
        return False

    if "geometry" not in cell:
        return False

    if "type" not in cell["geometry"]:
        return False

    if "coordinates" not in cell["geometry"]:
        return False

    # Validate cell data types
    if isinstance(cell["properties"]["index"], str) == False:
        return False

    if isinstance(cell["properties"]["centroid_lat"], float) == False:
        return False

    if isinstance(cell["properties"]["centroid_lon"], float) == False:
        return False

    if isinstance(cell["properties"]["resolution"], int) == False:
        return False

    if cell["geometry"]["type"] != "Polygon":
        return False

    if isinstance(cell["geometry"]["coordinates"], list) == False:
        return False   

    # Check coordinates structure
    if len(cell["geometry"]["coordinates"][0]) != 7:
        # Each polygon must be a hexagon with one extra point to close the shape.
        return False

    if len(cell["geometry"]["coordinates"][0][0]) != 2:
        # Each coordinate must be a pair.
        return False 

    if cell["geometry"]["coordinates"][0][0] != cell["geometry"]["coordinates"][0][-1]:
        # The first and last coordinate pair must be the same to close the shape.
        return False
    
    # Get the index from the cell
    index = cell["properties"]["index"]
    centroid = {
        "lat": cell["properties"]["centroid_lat"],
        "lon": cell["properties"]["centroid_lon"]
    }

    # Check that the index is correct from the centroid coordinates
    if h3.latlng_to_cell(centroid["lat"], centroid["lon"], h3_resolution) != index:
        return False

    return True
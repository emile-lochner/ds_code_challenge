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
        print("Invalid: Cell does not contain keyword 'type'.")
        return False

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

    # if "resolution" not in cell["properties"]:
    #     print("Invalid: Cell does not contain keyword 'properties:resolution'.")
    #     return False

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

    # if isinstance(cell["properties"]["resolution"], int) == False:
    #     print("Invalid: resolution is not int.")
    #     return False

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

    return True
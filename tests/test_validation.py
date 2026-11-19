import src.validation as val

validator = val.get_schema_validator("geojson_feature_schema.json")

test_cells = []
test_cells.append({
        'type': 'Feature', 
        'properties': {
            'index': '88ad361801fffff', 
            'centroid_lat': -33.859427322761434, 
            'centroid_lon': 18.677843311941835, 
            'resolution': 8
        }, 
        'geometry': {
            'type': 'Polygon', 
            'coordinates': [[
                [18.6811898997334, -33.86330279081797], 
                [18.683574296194426, -33.85928287732969], 
                [18.68022760998973, -33.85540739558428], 
                [18.67449676770625, -33.855551865779326], 
                [18.672112346191998, -33.85957172360946], 
                [18.675458791982372, -33.8634471669068], 
                [18.6811898997334, -33.86330279081797]
                ]]
            }
        })

test_cells.append({
        'type': 'Feature', 
        'properties': {
            'index': '88ad361801fffff', 
            'centroid_lat': -33.859427322761434, 
            'centroid_lon': 18.677843311941835, 
            'resolution': 8
        }
        })

test_cells.append({
        'type': 'Feature', 
        'properties': {
            'index': '88ad361801fffff', 
            'centroid_lon': 18.677843311941835, 
            'resolution': 8
        }, 
        'geometry': {
            'type': 'Polygon', 
            'coordinates': [[
                [18.6811898997334, -33.86330279081797], 
                [18.683574296194426, -33.85928287732969], 
                [18.68022760998973, -33.85540739558428], 
                [18.67449676770625, -33.855551865779326], 
                [18.672112346191998, -33.85957172360946], 
                [18.675458791982372, -33.8634471669068], 
                [18.6811898997334, -33.86330279081797]
                ]]
            }
        })

def test_check_h3_structure():
    global validator, test_cells

    assert val._check_h3_structure(test_cells[0]) == True
    assert val._check_h3_structure(test_cells[1]) == False
    assert val._check_h3_structure(test_cells[2]) == False
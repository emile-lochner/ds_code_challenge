import json
import sqlite3

feature = {
    "type": "Feature",
    "properties": {"name": "parcel_1"},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
    },
}

con = sqlite3.connect("geo.db")
con.enable_load_extension(True)
con.load_extension("path_to_geopoly")
con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS parcels USING geopoly(name)")

# Geopoly takes a single ring ([[x, y], ...]), so use the outer ring only
ring = feature["geometry"]["coordinates"][0]
con.execute(
    "INSERT INTO parcels(_shape, name) VALUES (?, ?)",
    (json.dumps(ring), feature["properties"]["name"]),
)
con.commit()

# Read back as JSON, and query by overlap with a bounding polygon
for name, shape in con.execute("SELECT name, geopoly_json(_shape) FROM parcels"):
    print(name, shape)

query = json.dumps([[5, 5], [15, 5], [15, 15], [5, 15]])
print(con.execute("SELECT name FROM parcels WHERE geopoly_overlap(_shape, ?)", (query,)).fetchall())
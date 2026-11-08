# Setting Up
## Windows
Your computer should have Python 3.12 or higher installed and correctly configured.
Once this is done, simply double click on the `win_setup.bat` script to create a virtual python environment and download all required packages.
Once this script has successfully run, double click on `win_run.bat` to run the data pipeline.

## Linux
Your computer should have Python 3.12 or higher installed and correctly configured.
In the terminal browse to the root directory of this repository and run the command
```bash
bash linux_setup.sh
```
to create a virtual python environment and download all required packages. 
Once this script has successfully completed run the command
```bash
bash linux_run.sh
```
to run the data pipeline.

# Task 1
## GeoJSON Schema and Validation
We expect the cell dictionary to have a specific structure as shown below:

```python
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
```

Of these the most critical for our purpose is the index, centroid coordinates and the geometry. If the cell is missing any of these properties it will be rejected. In practice, if we had either the centroid coordinates or the geometry polygon, we could recover the missing data by using the h3 python library (https://h3geo.org). However, it was considered out of scope for the purposes of this assignment.

Furthermore, the data was expected to be the types specified and if not would be considered corrupted and rejected. Once those hard cuts were completed we calculated two scores. To calculate the scores we rely on a reference cell which we obtained from the provided `city-hex-polygons-8.geojson` file. 

First, we calculate a distance score. For every 10 meter difference between the centroid coordinates we deduct 5% from the distance score down to a minimum of 0. Typically, GPS systems have an accuracy of approximately 10 meters, so this felt like a reasonable increment. This implies that with an offset of more than 200 meters the distance score would be zero. At the specified H3 resolution of 8 the hexagonal cells typically have a "diameter" of approximately 500 meters. This means that at the maximum distance of 200 meters we would still be in the same cell. 

Second, we calculate the polygon overlap score. The score is defined by the fraction of the test polygon area that overlaps the area of the reference polygon area. Complete overlap would produce a score of 1.0, while no overlap would produce a score of 0.0.

To calculate the total score we multiply the overlap and distance score. The total score is then compared with a threshold to decide if it should be rejected or not.
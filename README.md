# Setting Up and Running
## Windows
Your computer should have Python 3.12 or higher installed and correctly configured.
Once this is done, simply double click on the `win_setup.bat` script to create a virtual python environment and download all required packages.
Once this script has successfully run, double click on `win_run.bat` to run the data pipeline.

## Linux
Your computer should have Python 3.12 or higher installed and correctly configured.
On Ubuntu the venv module is packaged separately; install it if missing:
`sudo apt update && sudo apt install -y python3 python3-venv python3-pip`

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

# Task 1: Data Extraction
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

Furthermore, the data was expected to be the types specified and if not, would be considered corrupted and rejected. Once those hard cuts were completed we calculated two scores. To calculate the scores we rely on a reference cell which we obtained from the provided `city-hex-polygons-8.geojson` file. 

First, we calculate a distance score. For every 10 meter difference between the centroid coordinates we deduct 5% from the distance score down to a minimum of 0. Typically, GPS systems have an accuracy of approximately 10 meters, so this felt like a reasonable increment. This implies that with an offset of more than 200 meters the distance score would be zero. At the specified H3 resolution of 8 the hexagonal cells typically have a "diameter" of approximately 500 meters. This means that at the maximum distance of 200 meters we would still be in the same cell. 

Second, we calculate the polygon overlap score. The score is defined by the fraction of the test polygon area that overlaps the area of the reference polygon area. Complete overlap would produce a score of 1.0, while no overlap would produce a score of 0.0.

To calculate the total score we multiply the overlap and distance score. The total score is then compared with a threshold to decide if it should be rejected or not. I selected a default threshold of 0.95 to ensure high data quality while allowing minor deviation due to numerical error. In reality, the threshold would need to be selected based on the downstream task.

## Task 2: Initial Data Transformation
I relied heavily on SQLite databases for the data processing and storage. SQL is an very powerful tool that is essential to any data engineering environment and I felt it important to demonstrate my familiarity with databases. Databases provide reliable storage for all of a project's needs and allows reports to be generated without the need to run the data pipeline code. Letos (https://letos.org/) is an OpenSource program available for both Windows and Linux that will allow you to browse the database (automatically generated and stored in `data/database.db`) and create your own queries.

I was asked to include a threshold check to test the number of service requests that could successfully be assigned an H3 cell index. If a threshold could not not be met the program will terminate in an error state. I achieved a success rate of 74% mainly due to many of the service requests not containing GPS coordinates. Thus, I set a threshold of 70% to allow the program to continue running. The correct threshold to choose in practice will greatly depend on what this data will be used for and hence an arbitrary threshold is difficult to pick and defend. For example, if there is a suburb for which all GPS locations have not been included due to a systematic error it may pull the overall success rate down. If further analysis is heavily dependent on that suburb then the analysis cannot continue. However, if that suburb is not relevant for subsequent analysis then its contribution to the failure rate should not matter. If the failures are spread statistically evenly throughout Cape Town then as long as we still have a statistically significant number of samples, the analysis can continue. A threshold of 70% is still the majority of the data and with nearly a million service requests in the dataset, this should be enough data to allow most types of analyses.

## Task 5: Further Data Transformations
The assignment asked to get all the H3 cells within 1 minute of the Atlantis suburb. I interpreted that as 1 arc-minute (1 / 60 degrees) in both longitude and latitude.

To obtain the centroid coordinates of Atlantis, I did an API call to https://openstreetmap.org and searched for `Atlantis, Cape Town, South Africa`. This returned a GeoJSON polygon which represents the outline of the suburb. I then used a Python library called `shapely` to calculate the centroid coordinates.

The subset dataset was created by using the Euclidean distance between the centroid GPS coordinates and the GPS coordinates in the service records database table. I am aware that this is not a true distance, but given that the radius was given in arc-minutes and was quite small the error is expected to be minimal.

## Task 5: Anonymising Service Request Records
To anonymise the service requests, I made the following changes:
- Removed notification_number: Could be used to cross-reference other records to find the identity of the resident.
- Removed reference_number: Could be used to cross-reference other records to find the identity of the resident.
- Changed the creation and completion timestamps to be one of four values: 03:00, 09:00, 15:00, and 21:00. This is in line with the 6 hour temporal resolution required and gives analysts a way of determine if the request happened predawn, morning, afternoon or evening. Exact timestamps could possibly be used to cross reference with call logs to identify the resident.
- Removed GPS coordinates but kept the h3_level8_index. Exact GPS coordinates could be used to locate and identify the resident, while the H3 cells at level 8 resolution have an approximate radius of 500 meters. This is enough to obfuscate the location of the resident while still being useful for most analytical tasks and is within the 500 metre accuracy required by the assignment.

An anonymised CSV file will also be exported to `/export/anonymous.csv` once the pipeline is run as an example of what the resulting output would look like.
import time
from dotenv import load_dotenv

import data
import validation
import task1
import task2
import task5

# Load environment variables from the .env file in the root directory
load_dotenv()

# Constants that control parts of the pipeline
H3_RESOLUTION = 8
H3_LIMIT = -1 

print("-"*60)
print("CoCT Data Engineering Challenge")
print("-"*60)

data.download_data_files()

# ---------------------------------------------
# Task 1: Data Extraction
# ---------------------------------------------
print("Task 1: Data Extraction")
print("-"*60)
tic_start = time.perf_counter()

h3_cells_aws = task1.get_h3_cells_from_aws(H3_RESOLUTION, H3_LIMIT)
h3_cells_file = task1.get_h3_cells_from_file("data/city-hex-polygons-8.geojson", H3_LIMIT)
h3_cells_valid = validation.h3_validation(h3_cells_aws, h3_cells_file, H3_RESOLUTION)

task1.create_h3_cells_table()
task1.save_h3_cells_to_db(h3_cells_valid)

# Build a lookup of H3 indices to polygons. We will need this for Task 2
h3_cells_polygons = {}
for cell in h3_cells_valid:
    index = data.get_cell_index(cell)
    polygon = data.get_cell_vertices(cell)

    h3_cells_polygons[index] = data.geojson_to_polygon(polygon)

tic_end = time.perf_counter()
dt = tic_end - tic_start
print(f"\nTime taken for Task 1: {dt:.1f} seconds.")

# ---------------------------------------------
# Task 2: Initial Data Transformation
# ---------------------------------------------
print("\nTask 2: Initial Data Transformation")
print("-"*60)
tic_start = time.perf_counter()

task2.create_service_requests_table()
task2.create_service_requests_validation_table()
task2.join_service_requests_with_h3_cells(h3_cells_polygons)
task2.check_h3_assignment_success_threshold(0.7)
task2.validate_h3_indices()

tic_end = time.perf_counter()
dt = tic_end - tic_start
print(f"\nTime taken for Task 2: {dt:.1f} seconds.")

# ---------------------------------------------
# Task 5: Further Data Transformations
# ---------------------------------------------
print("\nTask 5: Further Data Transformations")
print("-"*60)
tic_start = time.perf_counter()

task5.get_wind_data()
task5.build_database_from_wind_xlsx()
atlantis_centroid = task5.get_suburb_centroid_coords("Atlantis, Cape Town, South Africa")
task5.create_requests_subset_for_wind_data(atlantis_centroid, arcminute_radius=1.0)
task5.add_wind_data_to_subset()
task5.anonymise_augmented_subsample_data()
task5.export_anonymous_csv_file()

tic_end = time.perf_counter()
dt = tic_end - tic_start
print(f"\nTime taken for Task5: {dt:.1f} seconds.")
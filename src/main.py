import data
import validation
import json

H3_RESOLUTION = 8

h3_cells = data.get_h3_cells(H3_RESOLUTION)

for cell in h3_cells:
    is_valid = validation.h3_validation(cell, H3_RESOLUTION)
    print(is_valid)
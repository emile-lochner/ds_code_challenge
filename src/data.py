import boto3
import h3
from dotenv import load_dotenv
import os
import json

# Load environment variables from the .env file in the root directory
load_dotenv()


def get_h3_cells(resolution):
    records_list = []

    # Get data from AWS
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"]
        )

    r = int(resolution)
    query = f'''SELECT * FROM S3Object[*].features[*] f WHERE f.properties.resolution = {r} LIMIT 10'''

    response = s3.select_object_content(
        Bucket="cct-ds-code-challenge-input-data",
        Key="city-hex-polygons-8-10.geojson",
        ExpressionType="SQL",
        Expression=query,
        InputSerialization={"JSON": {"Type": "DOCUMENT"}},
        OutputSerialization={"JSON": {}},
    )

    buffer = ""
    for event in response["Payload"]:
        if "Records" in event:
            buffer += event["Records"]["Payload"].decode("utf-8")
            *lines, buffer = buffer.split("\n")
            for line in lines:
                row = json.loads(line)  # one row as a dict
                records_list.append(row)

    return records_list


import boto3
from dotenv import load_dotenv
import os

# Load environment variables from the .env file in the root directory
load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET_KEY"]
    )

query = '''SELECT * FROM S3Object[*].features[*] f WHERE f.properties.resolution = 8'''

response = s3.select_object_content(
    Bucket="cct-ds-code-challenge-input-data",
    Key="city-hex-polygons-8-10.geojson",
    ExpressionType="SQL",
    Expression=query,
    InputSerialization={"JSON": {"Type": "DOCUMENT"}},
    OutputSerialization={"JSON": {}},
)

for event in response["Payload"]:
    if "Records" in event:
        print(event["Records"]["Payload"].decode("utf-8"))
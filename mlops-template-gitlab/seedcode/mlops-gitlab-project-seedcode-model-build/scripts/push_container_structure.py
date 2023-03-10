#!/usr/bin/env python

import os
import io
import sys
import yaml
import boto3
import pandas as pd

from model_package import ModelPackage

def put_object(resource: object, bucket: str, target_bucket: str, body: pd.DataFrame, prefix: str, key: str) -> dict:
    
    # convert contents to json format
    buffer = io.StringIO()
    body.to_json(buffer, orient="records")
    
    # get endpoint structure
    json_contents = buffer.getvalue()
    
    # save endpoint structure for endpoint deployment
    return resource.Object(bucket, "{}/{}".format(prefix,key)).put(Body=json_contents, ContentType='application/json')
    
if __name__ == '__main__':
    
    # READ CONFIG FILE
    with open("cfg/model_deploy.yaml") as f: config = yaml.load(f, Loader=yaml.SafeLoader)

    # SET VARIABLES (for testing...it still does not have the final filename intended by TFM team)
    bucket = os.getenv('BUCKET_NAME')
    model_group = config["endpoint"]["mlops_model"]["name"]
    filename = f"{os.getenv('FILENAME')}-version-latest.json"

    # GET MODEL GROUP NAME FROM CONFIG FILE
    try:
        # GET MODEL PACKAGE VERSION
        model_name = config["endpoint"]["mlops_model"]["name"] + "-" + os.getenv("TF_VAR_branch")
        obj = ModelPackage(model_name)
        version = obj.get_model_package_version()

        # EXTRACT CONTAINERS STRUCTURE
        body = obj.get_containers_structure(version)

        # PUSH CONTAINERS STRUCTURE INTO BUCKET
        s3 = boto3.resource("s3")
        response = put_object(s3, bucket=bucket, target_bucket=os.getenv("TARGET_BUCKET_NAME"), body=body, prefix= os.getenv("PREFIX_NAME"), key=filename)

        # GET RESPONSE STATUS CODE
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]

        if status_code==200:
            print("THE FILE {} HAS BEEN PUSHED SUCESSFULLY INTO THE BUCKET: {}".format(filename, bucket))
        else:
            print("THE FILE COULDN'T BEEN PUSHED INTO THE BUCKET - ERROR CODE: {}".format(status_code))

    except Exception as e:
        print("AN ERROR HAS BEEN FOUND \n {} ".format(repr(e)))
        sys.exit(1)

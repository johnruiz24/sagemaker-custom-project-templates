"""
Preprocessing code to be used in sagemaker client.

Input example:

input = {
  "product": "TFM",
  "channel": "WEB",
  "sourceMarket": "",
  "brand": "",
  "productType": "",
  "outDepartureAirport": "FRA",
  "outArrivalAirport": "JFK",
  "outDate": "2023-04-10T14:15:00",
  "outTime": "2023-04-10T14:15:00",
  "outCarrier": "WA | KL | DL | ",
  "outFlightNumber": "1768 | 0643 | 6106 | ",
  "outDuration": 650,
  "outSegments": 2,
  "inDepartureAirport": "JFK",
  "inArrivalAirport": "FRA",
  "inDate": "2023-04-16T19:40:00",
  "inTime": "2023-04-16T19:40:00",
  "inCarrier": "WA | KL | DL | ",
  "inFlightNumber": "1768 | 0643 | 6106 | ",
  "inDuration": 490,
  "inSegments": 1,
  "journeyType": "ROUNDTRIP",
  "tariffType": "PU",
  "fareBase": "",
  "corporateId": "",
  "baggage": "",
  "currency": "EUR",
  "vatPercentage": 0,
  "supplierPriceAdult": 690.71,
  "supplierPriceChild": 0,
  "supplierPriceInfant": 0,
  "adult": 1,
  "child": 0,
  "infant": 0,
  "source": "KL",
  "method": "MARGINBRAIN",
  "sessionId": "3a3874f1-927a-4ca7-b5a4-bd46f92fce5b",
  "requestId": "",
  "vcc": "KL",
  "event_type": "searchFlight"
}

"""


# Open source libraries
import os
import json
import joblib
import logging
import datetime
from random import random
import numpy as np
import pandas as pd
import tarfile
import re

try:
    from sagemaker_containers.beta.framework import (
        content_types,
        encoders,
        env,
        modules,
        transformer,
        worker,
        server,
    )
except ImportError:
    pass

# Holds the original input provided to the processing container
global RAW_INPUT_DATA
RAW_INPUT_DATA = {}

def input_fn(input_data, content_type):
    """Parse input data payload

    We currently only take json input. Since we need to process both labelled
    and unlabelled data we first determine whether the label column is present
    by looking to the provided data.
    """
    if content_type == "application/json":
        
        # Check raw json file
        print(input_data)
        global RAW_INPUT_DATA
        RAW_INPUT_DATA = json.loads(input_data)
        
        # Read the raw input data as a JSON file.
        df = pd.DataFrame(json.loads(input_data), index=[0])
        
        # do not forget to reset the index
        df.reset_index(inplace=True, drop = True)
        
        # Rename columns according to athena schema
        df['in_elapsed_flight_time'] = RAW_INPUT_DATA['inDuration']
        df['out_elapsed_flight_time'] = RAW_INPUT_DATA['outDuration']
        df['total_price'] = RAW_INPUT_DATA['supplierPriceAdult']
        df['total_markup_amount'] = random() * 50
        df['adt_numbers'] = RAW_INPUT_DATA['adult']
        df['cnn_numbers'] = RAW_INPUT_DATA['child']
        df['inf_numbers'] = RAW_INPUT_DATA['infant']
        df['journey_type'] = RAW_INPUT_DATA['journeyType']
        
        return df
    else:
        raise ValueError("{} not supported by script!".format(content_type))


def output_fn(prediction, accept):
    """Format prediction output

    The default accept/content-type between containers for serial inference is JSON.
    We also want to set the ContentType or mimetype as the same value as accept so the next
    container can read the response payload correctly.
    """
    if accept == "application/json":
        json_output = RAW_INPUT_DATA
        json_output["inference_data"] = [list(prediction[0])]
        print(json_output)

        return worker.Response(json.dumps(json_output), mimetype=accept)
    else:
        raise RuntimeException("{} accept type is not supported by this script.".format(accept))


def predict_fn(input_data, model):
    """Preprocess input data

    We implement this because the default predict_fn uses .predict(), but our model is a preprocessor
    so we want to use .transform().

    The output is returned in the following order:

        rest of features either one hot encoded or standardized
    """ 
    # scale and one-hot encode data from training process
    return model.transform(input_data)


def model_fn(model_dir):    
    """Deserialize fitted model"""
    preprocessor = joblib.load(os.path.join(model_dir, "model.joblib"))
    return preprocessor

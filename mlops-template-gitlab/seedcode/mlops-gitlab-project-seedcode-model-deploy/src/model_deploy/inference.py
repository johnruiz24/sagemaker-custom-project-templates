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
        
        return np.array(RAW_INPUT_DATA['inference_data'])
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
        json_output["prediction"] = prediction[0]
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
    # trained model inference
    print(input_data)
    print(model.predict(input_data))
    return model.predict(input_data)


def model_fn(model_dir):    
    """Deserialize fitted model"""
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    return model

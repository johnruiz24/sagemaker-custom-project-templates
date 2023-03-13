import os
import sys
import json
import joblib
import tarfile
import logging
import argparse
import pandas as pd

import boto3
import mlflow
import mlflow.sklearn

from sklearn import ensemble
from utils.mll_mlflow_api import Utils

logging.basicConfig(level=logging.INFO)

def train(args):
    
    # GET TRAINING AND TEST DATASET
    logging.info("READING DATA")
    X_train, y_train =  pd.read_csv(f"{args.x_train_folder}/X_train.csv"), pd.read_csv(f"{args.y_train_folder}/y_train.csv")
    X_test, y_test = pd.read_csv(f"{args.x_test_folder}/X_test.csv"), pd.read_csv(f"{args.y_test_folder}/y_test.csv")

    # SETTING NGINX HEADER AUTHENTICATION CREDENTIALS
    obj = Utils(args.region)
    hyperparameters = json.loads(args.hyperparameters)
    credentials = obj.retrieve_credentials(hyperparameters["mlflow_secrets"])
    os.environ['MLFLOW_TRACKING_USERNAME'] = credentials['username']
    os.environ['MLFLOW_TRACKING_PASSWORD'] = credentials['password']
    
    # SET MLFLOW API NAME 
    name = "{}-{}".format(hyperparameters["mlflow_api_name"], args.branch)
    # SET REMOTE MLFLOW SERVER
    mlflow.set_tracking_uri(obj.get_tracking_uri(name))
    mlflow.set_experiment(hyperparameters["experiment_name"])
    
    # enable autologging
    mlflow.sklearn.autolog()

    with mlflow.start_run():

        # TRAIN
        logging.info("TRAINING MODEL")
        model = ensemble.RandomForestClassifier(n_estimators=hyperparameters["n_estimators"],
                                                min_samples_leaf=hyperparameters["min_samples_leaf"],
                                                random_state=42)
        model.fit(X_train, y_train)

        # EVALUATE ACCURACY
        logging.info("EVALUATING MODEL")
        metrics = mlflow.sklearn.eval_and_log_metrics(model, 
                                                      X_test, 
                                                      y_test, 
                                                      prefix="test_")

    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--x-train-folder", type=str, default=os.environ["SM_CHANNEL_X_TRAIN"])
    parser.add_argument("--y-train-folder", type=str, default=os.environ["SM_CHANNEL_Y_TRAIN"])
    parser.add_argument("--x-test-folder", type=str, default=os.environ["SM_CHANNEL_X_TEST"])
    parser.add_argument("--y-test-folder", type=str, default=os.environ["SM_CHANNEL_Y_TEST"])
    parser.add_argument("--hyperparameters", type=str, default=os.environ["SM_HPS"])
    parser.add_argument("--output-folder", type=str, default=os.environ["SM_MODEL_DIR"])
    parser.add_argument("--branch", type=str, default="development")
    parser.add_argument("--region", type=str, default="eu-central-1")
    args, _ = parser.parse_known_args()
    
    # train model
    model = train(args)

    # save model
    joblib.dump(model, "model.joblib")
    with tarfile.open("/opt/ml/model/model.tar.gz", "w:gz") as tar_handle:
        tar_handle.add(f"model.joblib")

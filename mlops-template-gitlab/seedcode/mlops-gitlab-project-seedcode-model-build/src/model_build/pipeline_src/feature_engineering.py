import os
import joblib
import logging
import tarfile
import argparse
import pandas as pd
import numpy as np
import pyarrow

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)

def prepare_data(args, data):
    
    # GET DATASET FROM SCIKIT-LEARN
    logging.info("DEFINING SCIKIT-LEARN FEATURE ENGINEERING PIPELINE")

    # Assign atributes
    df = data.drop(['session_id',
                  'request_id',
                  'event_time',
                  'event',
                  'origin',
                  'destination',
                  'out_flight_numbers',
                  'departure_date',
                  'return_date',
                  'mkp_source'], 
                 axis=1)
    numeric_features = ['in_elapsed_flight_time',
                        'out_elapsed_flight_time',
                        'total_price',
                        'total_markup_amount',
                        'adt_numbers',
                        'cnn_numbers',
                        'inf_numbers']
    categorical_features = ['source']

    # Preprocess the data
    X = df.drop(args.target, axis=1)
    y = df[args.target]

    # Split the data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Define the pipeline
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))])

    preprocessor = ColumnTransformer(transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)])

    # Preprocessing
    pipeline_model = Pipeline(steps=[('preprocessor', preprocessor)])

    # Fit the pipeline to the training data
    pipeline_model.fit(X_train, y_train)
    
    # GET ONE HOT ENCODED COLUMN NAMES
    new_cat_cols = pipeline_model.named_steps["preprocessor"].named_transformers_["cat"].named_steps["onehot"].get_feature_names(categorical_features)
    
    # COLUNM NAMES OF PROCESSED DATA
    new_cols = np.concatenate([numeric_features, new_cat_cols])
    
    # PROCESS THE TRAINING AND TEST DATA
    X_train = pd.DataFrame(pipeline_model.transform(X_train), columns=new_cols)
    X_test = pd.DataFrame(pipeline_model.transform(X_test), columns=new_cols)
    
    # SAVE DATASET INTO CSV FILE
    logging.info("SAVE DATASET INTO CSV FILE")
    X_train.to_csv("{}/X_train.csv".format(os.getenv('x_train')), header=True, index=False)
    X_test.to_csv("{}/X_test.csv".format(os.getenv('x_test')), header=True, index=False)
    y_train.to_csv("{}/y_train.csv".format(os.getenv('y_train')), header=True, index=False)
    y_test.to_csv("{}/y_test.csv".format(os.getenv('y_test')), header=True, index=False)
    
    return pipeline_model

if __name__ == "__main__":
    base_dir = "/opt/ml/processing"
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=str, default="journey_type")
    parser.add_argument("--base_dir", type=str, default=base_dir)
    args, _ = parser.parse_known_args()
    
    # READ INPUT DATA
    pdInput = pd.read_parquet(os.environ['input_name'], engine = 'pyarrow')
    
    # GENERATE PREPROCESSING MODEL
    preprocessing_model = prepare_data(args, pdInput)
    
    # SAVE THE PREPROCESSING MODEL
    joblib.dump(preprocessing_model, "model.joblib")
    with tarfile.open(f"{base_dir}/model/model.tar.gz","w:gz") as tar_handle:
        tar_handle.add(f"model.joblib")
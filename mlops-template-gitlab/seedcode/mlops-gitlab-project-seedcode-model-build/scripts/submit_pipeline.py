import os
import sys
import yaml
import boto3
import logging
import argparse
import sagemaker

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.model_build.pipeline import get_pipeline

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Creates or updates and runs the pipeline for the pipeline script.")
    parser.add_argument("--run-execution", action="store_true")
    args, _ = parser.parse_known_args()

    # IAM ROLE
    iam_role = os.getenv("SAGEMAKER_ROLE")
    credentials = boto3.client('sts').assume_role(RoleArn=os.getenv("RUNNER_ROLE"), 
                                                  RoleSessionName="SagemakerSession")['Credentials']
    sagemaker_session = sagemaker.Session(boto3.session.Session(aws_access_key_id=credentials['AccessKeyId'],
                                                                aws_secret_access_key=credentials['SecretAccessKey'],
                                                                aws_session_token=credentials['SessionToken']),
                                          default_bucket = os.getenv("BUCKET_NAME"))
    # CONFIG
    with open(f"cfg/model_build.yaml") as f: config = yaml.load(f, Loader=yaml.SafeLoader)
    
    try:
        # INSTANTIATE PIPELINE
        logging.info("INSTANTIATE PIPELINE")
        pipeline = get_pipeline(iam_role=iam_role, session=sagemaker_session, cfg=config)
    
        # CREATE/UPDATE PIPELINE IN SAGEMAKER
        logging.info("CREATE/UPDATE PIPELINE IN SAGEMAKER")
        
        upsert_response = pipeline.upsert(role_arn=iam_role)
        logging.info(f"SAGEMAKER PIPELINE RESPONSE RECEIVED:\n {upsert_response}")

        if args.run_execution:
            # RUN PIPELINE
            logging.info("RUNNING PIPELINE")
            execution = pipeline.start()
            logging.info(f"EXECUTION STARTED WITH PipelineExecutionArn: {execution.arn}")
            
            logging.info("WAITING FOR THE EXECUTION TO FINISH...")
            execution.wait(360)

            logging.info(f"EXECUTION COMPLETED. SEE THE EXECUTION STEP DETAILS:\n {execution.list_steps()}")
    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

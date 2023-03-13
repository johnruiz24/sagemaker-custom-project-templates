# AWS api services setup
import os
import json
import boto3
import sagemaker

# Sagemaker pipeline dependencies
from sagemaker import PipelineModel
from sagemaker.sklearn.model import SKLearnModel
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.inputs import TrainingInput
from sagemaker.workflow.steps import TrainingStep
from sagemaker.tuner import ContinuousParameter, HyperparameterTuner
from sagemaker.workflow.steps import TuningStep
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.fail_step import FailStep
from sagemaker.workflow.functions import Join
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.conditions import ConditionLessThanOrEqualTo, ConditionEquals
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.steps import CacheConfig
from sagemaker.dataset_definition.inputs import AthenaDatasetDefinition
from sagemaker.dataset_definition.inputs import DatasetDefinition

# From custom code
from src.model_build import jobs
from src.utils.mll_mlflow_api import Utils

# Sagemaker pipeline definition
def get_pipeline(iam_role, session, cfg):
    
    # GET ASSIGNED BUCKET NAME
    default_bucket = session.default_bucket()
    
    # PARAMETERS FOR PIPELINE EXECUTION
    experiment_name = ParameterString(name='ExperimentName', 
                                      default_value=cfg["training"]["hyperparameters"]["experiment_name"])
    registered_model_name = ParameterString(name='RegisteredModelName', 
                                            default_value=cfg["training"]["hyperparameters"]["model_name"])
    
    # Create 1h cache for the sagemaker pipeline
    cache_config = CacheConfig(enable_caching=True, expire_after="PT1H")
    
    # Read input data from athena
    query = f"SELECT DISTINCT * FROM clean WHERE EVENT_TIME > current_date - interval '30' day"
    athena_dataset = AthenaDatasetDefinition(catalog=cfg["processing"]["catalog"],
                                             database=os.getenv('TF_VAR_branch') + '-' + cfg["processing"]["database"],
                                             query_string=query,
                                             output_s3_uri=f"s3://{default_bucket}/mlops_model_pipeline_input_data/",
                                             work_group="primary",
                                             output_format='PARQUET')
    dataset_def = DatasetDefinition(athena_dataset_definition=athena_dataset, local_path=cfg["processing"]["parameters"]["input_name"])

    
    # PROCESSING STEP
    processor = jobs.get_processor(iam_role=iam_role, session=session, cfg=cfg["processing"])
    step_process = ProcessingStep(name="PrepareData",
                                  processor=processor,
                                  code=cfg["processing"]["entry_point"],
                                  cache_config=cache_config,
                                  inputs = [ProcessingInput(destination="/opt/ml/processing/input", dataset_definition=dataset_def)],
                                  outputs=[
                                            ProcessingOutput(source=cfg["processing"]["parameters"]["model"], output_name="model"),
                                            ProcessingOutput(source=cfg["processing"]["parameters"]["x_train"], output_name="x_train"),
                                            ProcessingOutput(source=cfg["processing"]["parameters"]["y_train"], output_name="y_train"),
                                            ProcessingOutput(source=cfg["processing"]["parameters"]["x_test"], output_name="x_test"),
                                            ProcessingOutput(source=cfg["processing"]["parameters"]["y_test"], output_name="y_test")
                                           ])
    
    # GET TRAINING INPUT FROM PROCESSING OUTPUT
    x_training_input = TrainingInput(s3_data=step_process.properties.ProcessingOutputConfig.Outputs["x_train"].S3Output.S3Uri,
                                   content_type="text/csv")
    y_training_input = TrainingInput(s3_data=step_process.properties.ProcessingOutputConfig.Outputs["y_train"].S3Output.S3Uri,
                                   content_type="text/csv")
    x_test_input = TrainingInput(s3_data=step_process.properties.ProcessingOutputConfig.Outputs["x_test"].S3Output.S3Uri,
                                   content_type="text/csv")
    y_test_input = TrainingInput(s3_data=step_process.properties.ProcessingOutputConfig.Outputs["y_test"].S3Output.S3Uri,
                                   content_type="text/csv")

    # TRAINING STEP
    cfg["training"]["hyperparameters"]["experiment_name"] = cfg["training"]["hyperparameters"]["experiment_name"] + "-" + os.getenv('TF_VAR_branch')
    estimator = jobs.get_estimator(iam_role=iam_role, cfg=cfg["training"])
    step_train = TrainingStep(name="TrainModel",
                              estimator=estimator,
                              cache_config=cache_config,
                              inputs={"x_train": x_training_input, 
                                      "y_train": y_training_input,
                                      "x_test": x_test_input, 
                                      "y_test": y_test_input})
    
    # PRE-PROCESSING MODEL
    processor_model_path = "{}/model.tar.gz".format(step_process.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"])
    preprocessing_model = SKLearnModel(model_data=processor_model_path,
                                role=iam_role,
                                sagemaker_session=session,
                                source_dir=cfg['model_registry']['source_dir'],
                                entry_point=cfg["model_registry"]["preprocessing_inference"],
                                framework_version=cfg["processing"]["sklearn_framework_version"])
    
    # TRAINED MODEL
    sklearn_custom_model = SKLearnModel(framework_version=cfg["training"]["sklearn_framework_version"],
                                        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                                        sagemaker_session=session,
                                        source_dir=cfg['model_registry']['source_dir'],
                                        entry_point=cfg["model_registry"]["model_inference"],
                                        role=iam_role)
    
    # PRE-PROCESSING MODEL
    processor_model_path = "{}/model.tar.gz".format(step_process.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"])
    postprocessing_model = SKLearnModel(model_data=processor_model_path,
                                role=iam_role,
                                sagemaker_session=session,
                                source_dir=cfg['model_registry']['source_dir'],
                                entry_point=cfg["model_registry"]["postprocessing_inference"],
                                framework_version=cfg["processing"]["sklearn_framework_version"])
    
    # PIPELINE-MODEL DEFINITION
    pipeline_session = PipelineSession()
    model_registry_name = cfg['model_registry']['pipeline_name'] + "-" + os.getenv("TF_VAR_branch")
    pipeline_model = PipelineModel(name=model_registry_name,
                                   models=[preprocessing_model, sklearn_custom_model, postprocessing_model], 
                                   role=iam_role, 
                                   sagemaker_session=pipeline_session)
    
    
    # REGISTER PIPELINE-MODEL
    model_package_name = cfg['model_registry']['model_package_group_name'] + "-" + os.getenv("TF_VAR_branch")
    register_args = pipeline_model.register(content_types=["application/json"],
                                            response_types=["application/json"],
                                            inference_instances=[cfg['model_registry']['instance_type']],
                                            transform_instances=[cfg['model_registry']['instance_type']],
                                            model_package_group_name=model_package_name)
    
    step_pipeline_model = ModelStep(name="mlops",
                                    step_args=register_args)

    # CREATE PIPELINE INSTANCE
    pipeline = Pipeline(name=cfg["pipeline"]["name"]+"-"+os.getenv('TF_VAR_branch'), 
                        parameters=[experiment_name, registered_model_name], 
                        steps=[step_process, step_train, step_pipeline_model])
    
    return pipeline

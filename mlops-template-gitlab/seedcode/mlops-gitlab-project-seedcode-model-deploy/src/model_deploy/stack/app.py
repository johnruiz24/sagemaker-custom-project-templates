import os
import time
import yaml
import boto3
import sagemaker
from constructs import Construct
from model_package import ModelPackage
from aws_cdk import (aws_iam as iam,
                     aws_lambda as lambda_,
                     aws_apigateway as apigw,
                     aws_sagemaker as sagemaker_,
                     CfnOutput,
                     Duration,
                     Stack,
                     App)

def get_user_account() -> str:
    return boto3.client("sts").get_caller_identity()["Account"]

def get_model_location_from_ssm(ssm_parameter_name: str) -> str:
    response = boto3.client("ssm").get_parameter(Name=ssm_parameter_name)
    return response["Parameter"]["Value"]

class InferenceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # ==========================
        # ======== CONFIG  =========
        # ==========================
        # IAM ROLE FOR ENDPOINT
        iam_role = os.getenv("RUNNER_ROLE")
        bucket_name = sagemaker.Session().default_bucket()
        
        # READ CONFIG
        with open("../../../cfg/model_deploy.yaml") as file: config = yaml.load(file, Loader=yaml.SafeLoader)
        
        # GET GLOBAL PARAMETERS
        env = os.environ['DEPLOYMENT_ENV']
        endpoint_name = "{}-{}".format(config['endpoint']['name'], env)
        endpoint_config_name = "{}-{}".format(endpoint_name, int(time.time()))
        # ========================================
        # ===== SAGEMAKER MODEL - CONTAINERS =====
        # ========================================
        
        # DEFINE MODEL PACKAGE OBJECT FOR THE NON-AGG MODEL
        model_name = config["endpoint"]["mlops_model"]["name"] + "-" + os.getenv("TF_VAR_branch")
        obj = ModelPackage(model_name)

        # GET MODEL PACKAGE VERSION AND SET APPROVAL FOR ENDPOINT DEPLOYMENT
        version = obj.get_model_package_version()
        obj.update_model_version_status(version, "Approved")
        
        # CONFIGURE CONTAINER DEFINITION
        sagemaker_model_name_2 = "{}-{}-{}".format(model_name, version, env)
        container_2 = sagemaker_.CfnModel.ContainerDefinitionProperty(model_package_name=obj.get_model_package_arn(version))
        sagemaker_model_2 = sagemaker_.CfnModel(scope=self,
                                                id="Model2",
                                                execution_role_arn=iam_role,
                                                containers=[container_2],
                                                model_name=sagemaker_model_name_2)
         
        # =========================================
        # ===== SAGEMAKER PRODUCTION VARIANTS =====
        # =========================================
        product_variant_1 = sagemaker_.CfnEndpointConfig.ProductionVariantProperty(model_name=sagemaker_model_2.attr_model_name,
                                                                                   variant_name=config["endpoint"]["mlops_model"]["name"],
                                                                                   instance_type=config["endpoint"]["mlops_model"]["instance_type"],
                                                                                   initial_instance_count=config["endpoint"]["mlops_model"]["instance_count"],
                                                                                   initial_variant_weight=config["endpoint"]["mlops_model"]["initial_variant_weight"])

        # =====================================
        # ===== SAGEMAKER ENDPOINT CONFIG =====
        # =====================================
        sagemaker_endpoint_config = sagemaker_.CfnEndpointConfig(scope=self,
                                                                 id="EndpointConfig",
                                                                 production_variants=[product_variant_1],
                                                                 endpoint_config_name=endpoint_config_name,
                                                                 data_capture_config=sagemaker_.CfnEndpointConfig.DataCaptureConfigProperty(
                                                                     capture_content_type_header=sagemaker_.CfnEndpointConfig.CaptureContentTypeHeaderProperty(
                                                                        csv_content_types=["text/csv"]),
                                                                    capture_options=[
                                                                        sagemaker_.CfnEndpointConfig.CaptureOptionProperty(capture_mode="Input"),
                                                                        sagemaker_.CfnEndpointConfig.CaptureOptionProperty(capture_mode="Output")
                                                                    ],
                                                                    destination_s3_uri="s3://{}/mlflow_model/{}/endpoint-data-capture".format(bucket_name,endpoint_config_name),
                                                                    enable_capture=True,
                                                                    initial_sampling_percentage=100.0
                                                                ))
        # ==============================
        # ===== SAGEMAKER ENDPOINT =====
        # ==============================
        sagemaker_endpoint = sagemaker_.CfnEndpoint(scope=self,
                                                    id="Endpoint",
                                                    endpoint_config_name=sagemaker_endpoint_config.attr_endpoint_config_name,
                                                    endpoint_name=endpoint_name)
        sagemaker_endpoint.add_depends_on(sagemaker_endpoint_config)
        
        # ==================================================
        # ================ LAMBDA FUNCTION =================
        # ==================================================
        role = iam.Role.from_role_arn(scope=self, id="role", role_arn=iam_role)

        lambda_function = lambda_.Function(scope=self,
                                           id="lambda",
                                           role=role,
                                           function_name=endpoint_config_name,
                                           code=lambda_.Code.from_asset("lambda_function"),
                                           handler="handler.proxy",
                                           runtime=lambda_.Runtime.PYTHON_3_9,
                                           memory_size=128,
                                           timeout=Duration.seconds(120),
                                           environment={"ENDPOINT_NAME": endpoint_name})

        # ==================================================
        # ================== API GATEWAY ===================
        # ==================================================
        api = apigw.LambdaRestApi(scope=self,
                                  id="api_gateway",
                                  rest_api_name=endpoint_config_name,
                                  handler=lambda_function,
                                  proxy=True)

        # ==================================================
        # =================== OUTPUTS ======================
        # ==================================================
        CfnOutput(scope=self, id="APIURL", value=api.url)

app = App()
InferenceStack(app, f"mlops-template-{os.environ['DEPLOYMENT_ENV']}")
app.synth()

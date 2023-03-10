import time
import boto3
import logging
import pandas as pd

class ModelPackage(object):
    def __init__(self, model_group_name: str) -> None:
        self.client = boto3.client("sagemaker")
        self.model_group_name = model_group_name
        return
        
    def get_model_group_summary(self) -> pd.DataFrame():
        group = self.client.list_model_packages(ModelPackageGroupName=self.model_group_name)
        summary = pd.DataFrame.from_dict(group, orient="index").T.ModelPackageSummaryList.dropna()
        return pd.DataFrame(summary.tolist())
    
    def get_model_package_version(self, index: int=0) -> str:
        return self.get_model_group_summary().ModelPackageVersion.values[index]

    def get_model_package_arn(self, model_version: str="") -> str:
        df = self.get_model_group_summary()
        if not(model_version):
            model_version = self.get_model_package_version()
        model_package_arn = df[df["ModelPackageVersion"]==model_version]["ModelPackageArn"].values[0]
        return model_package_arn

    def update_model_version_status(self, model_version: str, status:str) -> None:
        model_package_arn = self.get_model_package_arn(model_version)
        self.client.update_model_package(ModelPackageArn=model_package_arn, ModelApprovalStatus=status)
        version_status = self.client.describe_model_package(ModelPackageName=model_package_arn)["ModelApprovalStatus"]
        while version_status != status:
            time.sleep(5)
        logging.info(f"MODEL PACKAGE VERSION {model_package_arn} HAS BEEN SUCCESSFULLY APPROVED")
        return  
    
    def get_containers_structure(self, model_version: str) -> pd.DataFrame():
        container = self.client.describe_model_package(ModelPackageName=self.get_model_package_arn(model_version))["InferenceSpecification"]["Containers"]
        return pd.DataFrame(container).drop(columns=["ImageDigest"])

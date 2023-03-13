#!/usr/bin/env python

import os
import json
import yaml
import boto3

def set_register_variant(client, endpoint_name, variant_name):

    response = client.register_scalable_target(ServiceNamespace="sagemaker",
                                               ResourceId="endpoint/{}/variant/{}".format(endpoint_name, variant_name),
                                               ScalableDimension="sagemaker:variant:DesiredInstanceCount",
                                               MinCapacity=1,
                                               MaxCapacity=10,
                                               RoleARN=os.getenv("SAGEMAKER_ROLE"),
                                               SuspendedState={
                                                   "DynamicScalingInSuspended": False,
                                                   "DynamicScalingOutSuspended": False,
                                                   "ScheduledScalingSuspended": False
                                               })
    return  
    
def set_scaling_policy(client, endpoint_name, variant_name, target_value, metric_type):
    response = client.put_scaling_policy(PolicyName="{}-autoscale-policy".format(variant_name),
                                         ServiceNamespace="sagemaker",
                                         ResourceId="endpoint/{}/variant/{}".format(endpoint_name, variant_name),
                                         ScalableDimension="sagemaker:variant:DesiredInstanceCount",
                                         PolicyType="TargetTrackingScaling",
                                         TargetTrackingScalingPolicyConfiguration={"TargetValue": target_value,
                                                                                   "PredefinedMetricSpecification": {
                                                                                                                     "PredefinedMetricType": metric_type
                                                                                                                    },
                                                                                   "ScaleOutCooldown": 30,
                                                                                   "ScaleInCooldown": 150})
    return
                                               
def wait_for_service(client, endpoint_name):

    waiter = client.get_waiter("endpoint_in_service")
    waiter.wait(EndpointName=endpoint_name)
    
    return

if __name__ == '__main__':
    # READ CONFIG FILE
    with open("cfg/model_deploy.yaml") as f: config = yaml.load(f, Loader=yaml.SafeLoader)
    
    # GET ENDPOINT NAME FROM CONFIG AND DEPLOYMENT ENVIRONMENT
    endpoint_name = f"{config['endpoint']['name']}-{os.getenv('DEPLOYMENT_ENV')}"
    
    # SET CLIENTS
    sm = boto3.client(service_name="sagemaker")
    autoscaling = boto3.client(service_name="application-autoscaling")
    
    # GET PRODUCTION VARIANTS
    response = sm.describe_endpoint(EndpointName=endpoint_name)
    variants = response['ProductionVariants']
    
    # REGISTER AUTOSCALING VARIANTS
    for variant in variants:
        print('REGISTERING VARIANT ... {}'.format(variant['VariantName']))
        try:
            # SET REGISTER SCALABLE TARGET 
            set_register_variant(autoscaling, endpoint_name=endpoint_name, variant_name=variant['VariantName'])
            wait_for_service(sm, endpoint_name)
            # SET VARIANT AUTOSCALING POLICY FOR TRACKING SCALING POLICY CONFIGURATION
            set_scaling_policy(autoscaling, endpoint_name=endpoint_name, variant_name=variant['VariantName'], target_value=10, metric_type="SageMakerVariantInvocationsPerInstance")
        except Exception as e: 
            print("AN ERROR HAS BEEN FOUND \n {} ".format(json.dumps({"error": repr(e)})))
    
    print("CHECK ENDPOINT CONFIGURATION:\n https://console.aws.amazon.com/sagemaker/home?region={}#/endpoints/{}".format(sm.meta.region_name, endpoint_name))

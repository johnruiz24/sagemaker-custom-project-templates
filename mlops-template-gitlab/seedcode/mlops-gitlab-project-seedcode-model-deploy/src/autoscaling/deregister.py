#!/usr/bin/env python

import os
import yaml
import boto3

def deregister_variant(client, endpoint_name, variant_name):
    
    response = client.deregister_scalable_target(ServiceNamespace='sagemaker',
                                                 ResourceId= 'endpoint/{}/variant/{}'.format(endpoint_name, variant_name),
                                                 ScalableDimension='sagemaker:variant:DesiredInstanceCount')
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
    
    # DEREGISTER AUTOSCALING FROM VARIANTS
    for variant in variants:
        print('DEREGISTERING VARIANT ... {}'.format(variant['VariantName']))
        try:
            deregister_variant(autoscaling, endpoint_name=endpoint_name, variant_name=variant['VariantName'])
            wait_for_service(sm, endpoint_name)
        except: 
            print("SEEMS LIKE IT WAS DEREGISTERED BEFORE")
    
    print("CHECK ENDPOINT CONFIGURATION:\n https://console.aws.amazon.com/sagemaker/home?region={}#/endpoints/{}".format(sm.meta.region_name, endpoint_name))



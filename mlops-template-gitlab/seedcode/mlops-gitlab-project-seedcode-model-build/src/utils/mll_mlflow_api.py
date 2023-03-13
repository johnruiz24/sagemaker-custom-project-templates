import sys
import json
import boto3
import pandas as pd

class Utils:
    def __init__(self, region_name):
        self.region_name = region_name
        return 
        
    def get_tracking_uri(self, name) -> str:
        client = boto3.client("apigatewayv2", region_name=self.region_name)
        try:
            df = pd.DataFrame.from_dict(client.get_apis()['Items'])
            tracking_uri = df[df.Name==name].ApiEndpoint.values[0]
        except KeyError as error: #THERE IS NOT EVEN ANY SINGLE APIGWV2 CONFIGURED
            print("AN ERROR HAS BEEN FOUND \n {} ".format(json.dumps({"error": repr(error)})))
            sys.exit(1)
        except IndexError as error: #MLFLOW API ENDPOINT WAS UNABLE TO BE RETRIEVED
            print("THERE ARE NO ACTIVE ENDPOINTS FOR MLFLOW-API")
            sys.exit(1)
        return tracking_uri
        
    def retrieve_credentials(self, secret_name) -> dict:
        client = boto3.client(service_name='secretsmanager', region_name=self.region_name)
        
        kwarg = {'SecretId': secret_name}
        secret = client.get_secret_value(**kwarg)
        credentials = {}
        
        credentials['username'] = json.loads(secret['SecretString'])['username']
        credentials['password'] = json.loads(secret['SecretString'])['password']
        return credentials

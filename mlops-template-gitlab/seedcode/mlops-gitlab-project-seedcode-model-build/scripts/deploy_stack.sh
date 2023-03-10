#!/usr/bin/env bash

# INSTALL NODE AND CDK
# sudo yum install -y gcc-c++ make
# curl -sL https://rpm.nodesource.com/setup_16.x | sudo bash -
# sudo yum install -y nodejs

# sudo npm install -g aws-cdk@2.41.0

# SET STAGE ENVIRONMENT VARIABLE TO USE IN THE CDK STACK
folder=$1
export DEPLOYMENT_ENV=$2

# CDK BOOTSTRAP AND DEPLOY
cd ${folder}
#ACCOUNT_ID=$(aws sts get-caller-identity --query Account | tr -d '"')
ACCOUNT_ID=$TF_VAR_aws_account_number
AWS_REGION=$(aws configure get region)

cdk bootstrap aws://${ACCOUNT_ID}/${AWS_REGION}
cdk deploy --require-approval never

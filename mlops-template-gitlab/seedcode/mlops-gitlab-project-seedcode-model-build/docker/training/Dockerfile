FROM continuumio/miniconda3:4.12.0

ENV PYTHONUNBUFFERED=TRUE

RUN apt-get --allow-releaseinfo-change update \
    && apt-get install build-essential -y

# install python dependencies
RUN pip install --no-cache --upgrade \
    boto3 \
    scikit-learn==1.1.2 \
    mlflow==1.30.0 \
    sagemaker-training==4.2.6

FROM python:3.9-slim

ENV PYTHONUNBUFFERED=TRUE

# install gcc
RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

# install python dependencies
RUN pip install --no-cache --upgrade \
    pandas==1.1.3 \
    scikit-learn==0.24.2 \
    sagemaker==2.105.0 \
    pyarrow \
    mlflow==1.30.0

import json
import pandas as pd
import requests
import boto3
from datetime import datetime
import time

# Constants
API_KEY = "47a22ce2c5e1ae43424d3af49890dd85"
S3_BUCKET = "ndepp-lambda-files"  # Your S3 bucket
S3_MAIN_FILE_PATH = "final_project/ML-Dataset.csv"  # Path to the main CSV file in S3
ROLE_ARN = "arn:aws:iam::123456789012:role/your-sagemaker-role"  # Replace with your SageMaker role
OUTPUT_PATH = "s3://ndepp-lambda-files/model-output/"  # Path for SageMaker model output

s3_client = boto3.client("s3")
sagemaker_client = boto3.client("sagemaker")
runtime_client = boto3.client("sagemaker-runtime")

def fetch_series_data(series_id):
    """
    Fetch observations for a given series ID from the FRED API.
    """
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        observations = data.get("observations", [])
        return pd.DataFrame(observations).rename(columns={"date": "ObservationDate", "value": series_id})
    else:
        raise Exception(f"Failed to fetch data for series {series_id}. Status code: {response.status_code}")

def merge_asof_closest_date(main_df, series_df, series_id):
    """
    Merge main dataframe with series dataframe by closest date using merge_asof.
    """
    main_df["OrderDate"] = pd.to_datetime(main_df["OrderDate"])
    series_df["ObservationDate"] = pd.to_datetime(series_df["ObservationDate"])

    series_df = series_df.sort_values(by="ObservationDate")
    main_df = main_df.sort_values(by="OrderDate")

    merged_df = pd.merge_asof(
        main_df,
        series_df[["ObservationDate", series_id]],
        left_on="OrderDate",
        right_on="ObservationDate",
        direction="nearest"
    )
    return merged_df.drop(columns=["ObservationDate"])

def upload_to_s3(dataframe, filename):
    """
    Upload the merged dataframe to S3 as a CSV file.
    """
    csv_data = dataframe.to_csv(index=False)
    s3_client.put_object(Bucket=S3_BUCKET, Key=filename, Body=csv_data)
    return f"s3://{S3_BUCKET}/{filename}"

def load_main_dataset():
    """
    Load the main dataset from S3.
    """
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_MAIN_FILE_PATH)
    return pd.read_csv(response['Body'])

def start_training_job(s3_data_path):
    """
    Start a SageMaker training job using the uploaded data.
    """
    training_job_name = f"training-job-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    response = sagemaker_client.create_training_job(
        TrainingJobName=training_job_name,
        AlgorithmSpecification={
            "TrainingImage": sagemaker.image_uris.retrieve("xgboost", boto3.Session().region_name),
            "TrainingInputMode": "File"
        },
        RoleArn=ROLE_ARN,
        InputDataConfig=[
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": s3_data_path,
                        "S3DataDistributionType": "FullyReplicated"
                    }
                },
                "ContentType": "text/csv"
            }
        ],
        OutputDataConfig={"S3OutputPath": OUTPUT_PATH},
        ResourceConfig={
            "InstanceType": "ml.m5.large",
            "InstanceCount": 1,
            "VolumeSizeInGB": 10
        },
        StoppingCondition={"MaxRuntimeInSeconds": 3600}
    )
    return training_job_name

def deploy_model(training_job_name):
    """
    Deploy the trained model as a SageMaker endpoint.
    """
    model_name = f"model-{training_job_name}"
    endpoint_name = f"endpoint-{training_job_name}"
    
    # Create model
    sagemaker_client.create_model(
        ModelName=model_name,
        PrimaryContainer={
            "Image": sagemaker.image_uris.retrieve("xgboost", boto3.Session().region_name),
            "ModelDataUrl": f"{OUTPUT_PATH}{training_job_name}/output/model.tar.gz"
        },
        ExecutionRoleArn=ROLE_ARN
    )
    
    # Deploy endpoint
    sagemaker_client.create_endpoint_config(
        EndpointConfigName=endpoint_name,
        ProductionVariants=[
            {
                "VariantName": "AllTraffic",
                "ModelName": model_name,
                "InstanceType": "ml.m5.large",
                "InitialInstanceCount": 1
            }
        ]
    )
    sagemaker_client.create_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_name
    )
    return endpoint_name

def lambda_handler(event, context):
    """
    Lambda handler to fetch data, preprocess, train, and deploy.
    """
    try:
        # Parse input for FRED series
        input_data = json.loads(event["body"])
        series_ids = input_data["series_ids"]

        # Load main dataset
        main_dataframe = load_main_dataset()

        # Fetch and merge series data
        for series_id in series_ids:
            series_data = fetch_series_data(series_id)
            series_data[series_id] = pd.to_numeric(series_data[series_id], errors="coerce")
            main_dataframe = merge_asof_closest_date(main_dataframe, series_data, series_id)

        # Drop rows with NA values
        main_dataframe = main_dataframe.dropna()

        # Upload preprocessed data to S3
        filename = f"merged_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        s3_data_path = upload_to_s3(main_dataframe, filename)

        # Start training job
        training_job_name = start_training_job(s3_data_path)

        # Wait for training to complete (simplified for demo; use Step Functions for production)
        time.sleep(3600)

        # Deploy the model
        endpoint_name = deploy_model(training_job_name)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Model trained and deployed successfully",
                "endpoint_name": endpoint_name
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

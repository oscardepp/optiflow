import json
import boto3
import configparser
import traceback
from datetime import datetime

# Load configurations from config-training.ini
config = configparser.ConfigParser()
config.read('config-training.ini')

# AWS Clients
sagemaker_client = boto3.client('sagemaker')

# Configurations
DB_HOST = config["rds"]["endpoint"]
DB_PORT = int(config["rds"]["port_number"])
DB_USER = config["rds"]["user_name"]
DB_PASSWORD = config["rds"]["user_pwd"]
DB_NAME = config["rds"]["db_name"]

BUCKET = config.get('s3', 'bucket_name')
SAGEMAKER_ROLE = config["sagemaker"]["role"]

def lambda_handler(event, context):
    """
    Lambda function to poll the status of a SageMaker training job.
    """
    try:
        # Step 1: Parse input from event
        if "body" not in event:
            raise ValueError("Missing 'body' in event")
        input_data = json.loads(event["body"])

        # Validate required fields
        if "training_job_name" not in input_data:
            raise ValueError("Missing required field: 'training_job_name'")

        training_job_name = input_data["training_job_name"]
        print(f"Polling status for training job: {training_job_name}")

        # Step 2: Get training job status from SageMaker
        response = sagemaker_client.describe_training_job(TrainingJobName=training_job_name)
        training_status = response["TrainingJobStatus"]
        print(f"Training job status: {training_status}")

        # Step 3: Handle job status
        if training_status in ["Completed", "Failed", "Stopped"]:
            # Job has completed, failed, or stopped
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": f"Training job {training_status}",
                    "training_job_name": training_job_name,
                    "status": training_status,
                    "details": response
                })
            }
        else:
            # Job is still in progress
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": f"Training job in progress: {training_status}",
                    "training_job_name": training_job_name,
                    "status": training_status
                })
            }

    except Exception as e:
        print("Error occurred in lambda_handler:")
        print(traceback.format_exc())  # Print the full traceback for debugging
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Failed to retrieve training job status",
                "error": str(e),
                "traceback": traceback.format_exc()  # Include full traceback in the response for debugging
            })
        }

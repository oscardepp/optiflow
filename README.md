# Optiflow 

Optiflow is a REST API that is a predictive inventory management system used to automatically train and do inference on financial datasets once uploaded. The high-level goals of this project include:  

- Interact with FRED API -important for economic data
- Explore how Sagemaker works
- Make predictions more accessible by just specifying file to upload and coming up with insights related to Sagemaker 
- Train models without compute on amazon servers


## High-level depiction of project 

<p align="center">
  <img src="https://github.com/user-attachments/assets/56118e18-3bf4-498c-8ead-794d1c4b12a0" alt="highlevel" width="800"/>
</p>
<p align="center"><sub><i>Figure 1. A depiction illustrating the interactions between the user, events, lambda functions and API calls involved in Optiflow.</i></sub></p>


## Database design 

<p align="center">
  <img src="https://github.com/user-attachments/assets/b1aa0af6-24ff-475f-b8e1-cab134c5ff07" alt="Odor Leak Simulation" width="400"/>
</p>
<p align="center"><sub><i>Figure 2. SQL Tables within the SalesDB database listing the uploaded and processed datasets, the models used for training and inference, and the jobs showing the status of training and inference. </i></sub></p>

## 1. Preprocess data with FRED API 

Ask client what data they want to append to dataset. This involves three computations after the data is uploaded to a S3 bucket
1. Query FRED API based on input data types, sort and return info
2. Merging queried FRED API data based on OrderDate (pandas function)
3. Split into training and testing set (randomly shuffle and return two datasets) 
Uploads 3 datasets to S3 as in typical ML tasks:	
Train        (2)   Test         (3)   Real-y values

## 2. Train model using Sagemaker

Input hyperparameters, dataset_id of the training set. 
XGBoost is a prebuilt image on us-east-2 that we feed into Sagemaker, along with hyperparameters provided. 
Our API is asynchronous in nature because of the time intensive nature of training a ML task using Sagemaker. As we recall from class, server gives a response, but may take longer to give a completed response, we initiate a sagemaker job  as in Project03

## 3. Poll Model Status 

For asynchronous APIs, we must keep track of a job to poll status. We get the job status from Sagemaker, updating the job’s status in our jobs table in the database everytime we check status
When completed, Sagemaker uploads the model (.tar.gz) to S3, and we reflect this change in our models table and in our jobs table. 

## 4. Prediction/inference using Sagemaker

Prediction using the model we trained and our test dataset (unseen)
Given these inputs, pass a job to Sagemaker to execute prediction by registering a job, then running the job, updating our jobs table to reflect this new job

Our API is asynchronous in nature because of the time intensive nature of predicting a ML task using Sagemaker. Server gives a response, but may take longer to give a completed response, we keep track of inference jobs. 

## 5. Results 

Compute the mean-squared-error metric between our real y and our prediction data. This featuer calls for the dataset ids and compute the result and returns it. 


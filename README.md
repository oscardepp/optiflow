# Optiflow API 
Inventory shortages and excess stock are critical challenges faced in regions with
limited technological infrastructure, leading to increased costs, waste, and missed
opportunities. We developed a predictive inventory management system leveraging
AWS services for scalability, efficiency, and automation to address this, with the overall
workflow represented in Figure 1. 

- Interact with FRED API -important for economic data
- Explore how Sagemaker works
- Make predictions more accessible by just specifying file to upload and coming up with insights related to Sagemaker 
- Train models without compute on amazon servers


## High-level depiction of project 

<p align="center">
  <img src="https://github.com/user-attachments/assets/56118e18-3bf4-498c-8ead-794d1c4b12a0" alt="highlevel" width="800"/>
</p>
<p align="center"><sub><i>Figure 1. A depiction illustrating the interactions between the user, events, lambda functions and API calls involved in Optiflow.</i></sub></p>

Our system employs an asynchronous RESTful API architecture implemented through
AWS API Gateway, integrating various AWS services. Key data components like
historical inventory levels, sales data, and supply chain variables make up the input
dataset, storing the files in S3 and information in RDS, which is organized into datasets,
models, and jobs tables, where jobs are Sagemaker jobs defining whether the training
or inference is done yet or not. User interactions flow through a streamlined process
described in the next section using lambda functions to achieve these functionalities.
## Database design 

<p align="center">
  <img src="https://github.com/user-attachments/assets/b1aa0af6-24ff-475f-b8e1-cab134c5ff07" alt="Odor Leak Simulation" width="400"/>
</p>
<p align="center"><sub><i>Figure 2. SQL Tables within the SalesDB database listing the uploaded and processed datasets, the models used for training and inference, and the jobs showing the status of training and inference. </i></sub></p>


## Explanation of Server-side Functions
The system begins with data ingestion and preprocessing, where input files are
uploaded and enhanced with additional features such as 10-year yield and volatility,
which are user-inputted(/preprocess). We don’t memorize the series ID/ticker of each series
and there are a lot of tickers, so we ask clients for keywords of the series they want and order
by popularity so we can select the series that is most used. We do this by interacting with the
FRED API. For example, if we want to look at the 10-year yields, an indicator of economic
health, we type this into the client app, using the query /search?search
_
text=10+year+yield. We
encode the parameter by using the function urlencode for the FRED API call. There are a lot of
results so we pageify the results into 10 results/page ordering by popularity so the client doesn't
have to scroll a lot to get to the most used ticker. These additional features are taken from
FRED’s API and a column is appended to the user’s inputted data matching the
OrderDate with the feature’s date. The null values are filtered out in this function. The
preprocessed data is stored in Amazon S3, generating a dataset_id for tracking.
Users can then initiate model training via an API call(/training/train), using the
dataset_id and hyperparameters as input for a model (a tree-based XGBoost model)
through AMSagemaker, which produces a job_id. Polling functions that poll whether training
is done is important because training often takes longer than the 15 minutes than lambda
function allow. The status of this job can be checked by users by polling for the training
status that Sagemaker is running(/training/{job_id}).
Once the model is trained, SageMaker is utilized to test and deploy it. Predictions are
generated through API calls using the model_id and dataset_id, resulting in a job_id that
links to the prediction results (/inference/{job_id}). The error of the model prediction can
be retrieved as well once the predictions are uploaded, inputting a truth value dataset
and predictions dataset (/results/{actual_y_id}{prediction_id}) There is also an
embedded functionality that reset the database to default settings(/reset). Every
dataset, model, and job can also be retrieved via GET methods (/dataset, /models,
/jobs).
## Other features
We moved away from access keys by directly attaching policies to the lambda functions,
enabling us to test faster, with one user authorized to test this function. We added a
Sagemaker role with full permissions to allow Sagemaker to help with this. Another
extension of this project would be to restrict a user to only be able to view/add the
processed and predicted results of the model, reinforcing the least privileges of each
user. We attempted to use REST API features by posting.


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
Our API is asynchronous in nature because of the time intensive nature of training a ML task using Sagemaker. As we recall from class, server gives a response, but may take longer to give a completed response, we initiate a sagemaker job. 

## 3. Poll Model Status 

For asynchronous APIs, we must keep track of a job to poll status. We get the job status from Sagemaker, updating the job’s status in our jobs table in the database everytime we check status
When completed, Sagemaker uploads the model (.tar.gz) to S3, and we reflect this change in our models table and in our jobs table. 

## 4. Prediction/inference using Sagemaker

Prediction using the model we trained and our test dataset (unseen)
Given these inputs, pass a job to Sagemaker to execute prediction by registering a job, then running the job, updating our jobs table to reflect this new job

Our API is asynchronous in nature because of the time intensive nature of predicting a ML task using Sagemaker. Server gives a response, but may take longer to give a completed response, we keep track of inference jobs. 

## 5. Results 

Compute the mean-squared-error metric between our real y and our prediction data. This featuer calls for the dataset ids and compute the result and returns it. 


@echo off
REM Cloud Run Deployment Script for Windows
REM This script deploys all services to Google Cloud Run

setlocal EnableDelayedExpansion

REM Configuration
set PROJECT_ID=your-project-id
set REGION=us-central1
set BACKEND_IMAGE=hamid2019/flask-react-backend:latest
set FRONTEND_IMAGE=hamid2019/flask-react-frontend:latest

echo Starting Cloud Run deployment...

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: gcloud CLI is not installed
    echo Install it from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Check if project is set
if "%PROJECT_ID%"=="your-project-id" (
    echo Error: Please set your PROJECT_ID in this script
    pause
    exit /b 1
)

REM Set the project
echo Setting project to %PROJECT_ID%...
gcloud config set project %PROJECT_ID%

REM Enable required APIs
echo Enabling required APIs...
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo Deploying backend services...

REM Deploy READ service
echo Deploying READ service...
gcloud run deploy flask-read --image=%BACKEND_IMAGE% --region=%REGION% --platform=managed --allow-unauthenticated --set-env-vars="SERVICE_TYPE=read" --max-instances=50 --concurrency=100 --memory=512Mi --cpu=1 --timeout=300 --quiet

REM Deploy WRITE service
echo Deploying WRITE service...
gcloud run deploy flask-write --image=%BACKEND_IMAGE% --region=%REGION% --platform=managed --allow-unauthenticated --set-env-vars="SERVICE_TYPE=write" --max-instances=20 --concurrency=50 --memory=512Mi --cpu=1 --timeout=300 --quiet

REM Deploy OPERATIONS service
echo Deploying OPERATIONS service...
gcloud run deploy flask-operations --image=%BACKEND_IMAGE% --region=%REGION% --platform=managed --allow-unauthenticated --set-env-vars="SERVICE_TYPE=operations" --max-instances=30 --concurrency=80 --memory=512Mi --cpu=1 --timeout=300 --quiet

REM Deploy FRONTEND service
echo Deploying FRONTEND service...
gcloud run deploy flask-frontend --image=%FRONTEND_IMAGE% --region=%REGION% --platform=managed --allow-unauthenticated --max-instances=10 --concurrency=200 --memory=256Mi --cpu=1 --timeout=60 --quiet

echo Getting service URLs...

REM Get service URLs
for /f %%i in ('gcloud run services describe flask-read --region=%REGION% --format="value(status.url)"') do set READ_URL=%%i
for /f %%i in ('gcloud run services describe flask-write --region=%REGION% --format="value(status.url)"') do set WRITE_URL=%%i
for /f %%i in ('gcloud run services describe flask-operations --region=%REGION% --format="value(status.url)"') do set OPS_URL=%%i
for /f %%i in ('gcloud run services describe flask-frontend --region=%REGION% --format="value(status.url)"') do set FRONTEND_URL=%%i

echo.
echo Deployment complete!
echo.
echo Service URLs:
echo Frontend:   %FRONTEND_URL%
echo READ API:   %READ_URL%
echo WRITE API:  %WRITE_URL%
echo OPS API:    %OPS_URL%
echo.
echo Next steps:
echo 1. Set up Load Balancer to route requests (see CLOUD_RUN_DEPLOYMENT.md)
echo 2. Configure environment variables for each service
echo 3. Set up custom domain (optional)
echo.
pause
#!/bin/bash

# Cloud Run Deployment Script
# This script deploys all services to Google Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID="your-project-id"
REGION="us-central1"
BACKEND_IMAGE="hamid2019/flask-react-backend:latest"
FRONTEND_IMAGE="hamid2019/flask-react-frontend:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Cloud Run deployment...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if project is set
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo -e "${RED}Error: Please set your PROJECT_ID in this script${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}Setting project to $PROJECT_ID...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo -e "${YELLOW}Deploying backend services...${NC}"

# Deploy READ service (2 instances for load balancing)
echo -e "${YELLOW}Deploying READ service...${NC}"
gcloud run deploy flask-read \
    --image=$BACKEND_IMAGE \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="SERVICE_TYPE=read" \
    --max-instances=50 \
    --concurrency=100 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --quiet

# Deploy WRITE service
echo -e "${YELLOW}Deploying WRITE service...${NC}"
gcloud run deploy flask-write \
    --image=$BACKEND_IMAGE \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="SERVICE_TYPE=write" \
    --max-instances=20 \
    --concurrency=50 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --quiet

# Deploy OPERATIONS service
echo -e "${YELLOW}Deploying OPERATIONS service...${NC}"
gcloud run deploy flask-operations \
    --image=$BACKEND_IMAGE \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="SERVICE_TYPE=operations" \
    --max-instances=30 \
    --concurrency=80 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --quiet

# Deploy FRONTEND service
echo -e "${YELLOW}Deploying FRONTEND service...${NC}"
gcloud run deploy flask-frontend \
    --image=$FRONTEND_IMAGE \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --max-instances=10 \
    --concurrency=200 \
    --memory=256Mi \
    --cpu=1 \
    --timeout=60 \
    --quiet

echo -e "${GREEN}Getting service URLs...${NC}"

# Get service URLs
READ_URL=$(gcloud run services describe flask-read --region=$REGION --format="value(status.url)")
WRITE_URL=$(gcloud run services describe flask-write --region=$REGION --format="value(status.url)")
OPS_URL=$(gcloud run services describe flask-operations --region=$REGION --format="value(status.url)")
FRONTEND_URL=$(gcloud run services describe flask-frontend --region=$REGION --format="value(status.url)")

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Service URLs:"
echo "Frontend:   $FRONTEND_URL"
echo "READ API:   $READ_URL"
echo "WRITE API:  $WRITE_URL"
echo "OPS API:    $OPS_URL"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Set up Load Balancer to route requests (see CLOUD_RUN_DEPLOYMENT.md)"
echo "2. Configure environment variables for each service"
echo "3. Set up custom domain (optional)"
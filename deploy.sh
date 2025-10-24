#!/bin/bash
# Cloud Run Deployment Script for Education Insights Agent System

set -e  # Exit on error

echo "=========================================="
echo "🚀 Education Insights - Cloud Run Deploy"
echo "=========================================="

# Source environment variables
if [ -f "set_env.sh" ]; then
    echo "📝 Loading environment variables..."
    source set_env.sh
else
    echo "⚠️  set_env.sh not found. Using defaults..."
    export PROJECT_ID="qwiklabs-gcp-04-b5171aa68bec"
    export REGION="us-west1"
    export REPO_NAME="instavibe-agents"
fi

# Configuration
SERVICE_NAME="education-insights-agent"
IMAGE_NAME="education-insights"
ARTIFACT_REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}"

echo ""
echo "Configuration:"
echo "  Project ID: ${PROJECT_ID}"
echo "  Region: ${REGION}"
echo "  Service: ${SERVICE_NAME}"
echo "  Image: ${ARTIFACT_REGISTRY}"
echo ""

# Confirm deployment
read -p "Deploy to Cloud Run? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "=========================================="
echo "📦 Step 1: Building Docker Image"
echo "=========================================="

# Build using Cloud Build (faster, uses Google's infrastructure)
gcloud builds submit \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --tag ${ARTIFACT_REGISTRY}:latest \
    --timeout=20m

echo ""
echo "=========================================="
echo "🚢 Step 2: Deploying to Cloud Run"
echo "=========================================="

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --image=${ARTIFACT_REGISTRY}:latest \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
    --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \
    --set-env-vars="BIGQUERY_DATASET=education_data" \
    --service-account=${SERVICE_ACCOUNT_NAME}

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --format='value(status.url)')

echo ""
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "Test endpoints:"
echo "  Health: ${SERVICE_URL}/health"
echo "  Chat UI: ${SERVICE_URL}/"
echo "  API Docs: ${SERVICE_URL}/docs"
echo ""
echo "=========================================="


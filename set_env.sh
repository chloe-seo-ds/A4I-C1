#!/bin/bash
# Google Cloud Project Configuration
export PROJECT_ID="qwiklabs-gcp-04-b5171aa68bec"
export PROJECT_NUMBER="658656814425"
export SERVICE_ACCOUNT_NAME="qwiklabs-gcp-04-b5171aa68bec@qwiklabs-gcp-04-b5171aa68bec.iam.gserviceaccount.com"

# Spanner Configuration
export SPANNER_INSTANCE_ID="edequity-spanner"
export SPANNER_DATABASE_ID="school_data"

# Google AI Configuration
export GOOGLE_CLOUD_PROJECT="qwiklabs-gcp-04-b5171aa68bec"
export GOOGLE_GENAI_USE_VERTEXAI="TRUE"
export GOOGLE_CLOUD_LOCATION="us-west1"

# Artifact Registry Configuration
export REPO_NAME="instavibe-agents"
export REGION="us-west1"

# Load secrets (API keys, tokens, etc.)
# These are stored separately for security
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/secrets/maps_api_key.txt" ]; then
    export GOOGLE_MAPS_API_KEY=$(cat "${SCRIPT_DIR}/secrets/maps_api_key.txt" | tr -d '\n')
else
    echo "⚠️  Warning: secrets/maps_api_key.txt not found"
fi

# Display confirmation
echo "=========================================="
echo "✅ Environment Variables Set Successfully"
echo "=========================================="
echo "  PROJECT_ID: ${PROJECT_ID}"
echo "  PROJECT_NUMBER: ${PROJECT_NUMBER}"
echo "  SPANNER_INSTANCE_ID: ${SPANNER_INSTANCE_ID}"
echo "  SPANNER_DATABASE_ID: ${SPANNER_DATABASE_ID}"
echo "  GOOGLE_CLOUD_LOCATION: ${GOOGLE_CLOUD_LOCATION}"
echo "  REPO_NAME: ${REPO_NAME}"
echo "  REGION: ${REGION}"
if [ -n "${GOOGLE_MAPS_API_KEY}" ]; then
    echo "  GOOGLE_MAPS_API_KEY: ${GOOGLE_MAPS_API_KEY:0:20}... ✅"
else
    echo "  GOOGLE_MAPS_API_KEY: NOT SET ⚠️"
fi
echo "=========================================="

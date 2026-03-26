#!/bin/bash
# =============================================================================
# AI Learning Assistant — Elastic Beanstalk Deployment Script
# Usage: chmod +x deploy-eb.sh && ./deploy-eb.sh
# =============================================================================

set -e

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
APP_NAME="ai-learning-assistant"
ENV_NAME="ai-learning-env"
REGION="ap-south-1"
PLATFORM="python-3.11"
INSTANCE_TYPE="t3.small"
TABLE_PREFIX="ai-learning-"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   AI Learning Assistant — Elastic Beanstalk Deploy   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── CHECK PREREQUISITES ──────────────────────────────────────────────────────
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v eb &> /dev/null; then
    echo -e "${RED}ERROR: AWS EB CLI not found.${NC}"
    echo "Install it with: pip install awsebcli"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found.${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS credentials not configured.${NC}"
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: ${ACCOUNT_ID}${NC}"
echo -e "${GREEN}✓ Region: ${REGION}${NC}"

# ─── INITIALIZE EB APP ────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/6] Initializing Elastic Beanstalk application...${NC}"

if [ ! -f ".elasticbeanstalk/config.yml" ]; then
    eb init "${APP_NAME}" \
        --platform "${PLATFORM}" \
        --region "${REGION}" \
        --no-interactive
    echo -e "${GREEN}✓ EB application initialized: ${APP_NAME}${NC}"
else
    echo -e "${GREEN}✓ EB application already initialized${NC}"
fi

# ─── CREATE DynamoDB TABLES ───────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/6] Setting up DynamoDB tables...${NC}"

TABLES=(
    "ai-learning-users"
    "ai-learning-sessions"
    "ai-learning-quizzes"
    "ai-learning-flashcards"
    "ai-learning-achievements"
    "ai-learning-study-rooms"
)

for TABLE in "${TABLES[@]}"; do
    if aws dynamodb describe-table --table-name "${TABLE}" --region "${REGION}" &> /dev/null; then
        echo -e "${GREEN}✓ Table exists: ${TABLE}${NC}"
    else
        aws dynamodb create-table \
            --table-name "${TABLE}" \
            --attribute-definitions AttributeName=id,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "${REGION}" &> /dev/null
        echo -e "${GREEN}✓ Created table: ${TABLE}${NC}"
    fi
done

# ─── CREATE OR UPDATE EB ENVIRONMENT ─────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/6] Creating/updating Elastic Beanstalk environment...${NC}"

if eb status "${ENV_NAME}" &> /dev/null 2>&1; then
    echo -e "${CYAN}→ Deploying update to existing environment: ${ENV_NAME}${NC}"
    eb deploy "${ENV_NAME}" --timeout 20
else
    echo -e "${CYAN}→ Creating new environment: ${ENV_NAME}${NC}"
    eb create "${ENV_NAME}" \
        --instance-type "${INSTANCE_TYPE}" \
        --region "${REGION}" \
        --timeout 20
fi

# ─── SET ENVIRONMENT VARIABLES ────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] Configuring environment variables...${NC}"

eb setenv \
    AWS_REGION="${REGION}" \
    TABLE_PREFIX="${TABLE_PREFIX}" \
    STRICT_MODE="false" \
    -e "${ENV_NAME}"

echo -e "${GREEN}✓ Environment variables configured${NC}"

# ─── GET DEPLOYMENT URL ───────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[6/6] Retrieving deployment URL...${NC}"

EB_URL=$(eb status "${ENV_NAME}" | grep "CNAME" | awk '{print $2}')

if [ -z "$EB_URL" ]; then
    EB_URL=$(aws elasticbeanstalk describe-environments \
        --environment-names "${ENV_NAME}" \
        --region "${REGION}" \
        --query "Environments[0].CNAME" \
        --output text)
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    DEPLOYMENT SUCCESSFUL! 🎉                     ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Backend URL:  http://${EB_URL}${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}║  NEXT STEP: Set this in Vercel environment variables:            ║${NC}"
echo -e "${GREEN}║  REACT_APP_API_URL=http://${EB_URL}${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Health check: curl http://${EB_URL}/health${NC}"
echo ""

# Save URL to file for easy reference
echo "http://${EB_URL}" > .eb-backend-url.txt
echo -e "${GREEN}✓ Backend URL saved to .eb-backend-url.txt${NC}"

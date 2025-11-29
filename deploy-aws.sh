#!/bin/bash

# Email2KG AWS Deployment Script
# This script helps deploy Email2KG to AWS ECS/Fargate

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Email2KG AWS Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
    echo "Installation: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install it first.${NC}"
    echo "Installation: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Get AWS Account ID and Region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo ""

# Prompt for deployment type
echo "Select deployment type:"
echo "1) ECS Fargate (Recommended for production)"
echo "2) EC2 (Manual setup required)"
echo "3) Docker Compose (Local testing only)"
read -p "Enter choice [1-3]: " deployment_type

case $deployment_type in
    1)
        echo -e "${GREEN}Deploying to ECS Fargate...${NC}"

        # Create ECR repositories if they don't exist
        echo "Creating ECR repositories..."
        aws ecr describe-repositories --repository-names email2kg-backend || \
            aws ecr create-repository --repository-name email2kg-backend

        aws ecr describe-repositories --repository-names email2kg-frontend || \
            aws ecr create-repository --repository-name email2kg-frontend

        # Login to ECR
        echo "Logging in to ECR..."
        aws ecr get-login-password --region $AWS_REGION | \
            docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

        # Build and push backend
        echo "Building backend image..."
        docker build -t email2kg-backend ./backend
        docker tag email2kg-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/email2kg-backend:latest

        echo "Pushing backend image to ECR..."
        docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/email2kg-backend:latest

        # Build and push frontend
        echo "Building frontend image..."
        docker build -t email2kg-frontend ./frontend
        docker tag email2kg-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/email2kg-frontend:latest

        echo "Pushing frontend image to ECR..."
        docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/email2kg-frontend:latest

        echo -e "${GREEN}✓ Images pushed to ECR successfully!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Create RDS PostgreSQL database"
        echo "2. Create ECS cluster: aws ecs create-cluster --cluster-name email2kg-cluster"
        echo "3. Create task definitions (see AWS_DEPLOYMENT.md)"
        echo "4. Create ECS service"
        echo ""
        echo "See AWS_DEPLOYMENT.md for detailed instructions."
        ;;

    2)
        echo -e "${YELLOW}EC2 Deployment Selected${NC}"
        echo ""
        echo "Manual steps required:"
        echo "1. Launch EC2 instance (t3.medium recommended)"
        echo "2. SSH to instance: ssh -i your-key.pem ubuntu@EC2_IP"
        echo "3. Follow instructions in AWS_DEPLOYMENT.md (Option 2)"
        echo ""
        read -p "Press Enter to see EC2 instance launch command..."
        echo ""
        echo "aws ec2 run-instances \\"
        echo "  --image-id ami-0c55b159cbfafe1f0 \\"
        echo "  --instance-type t3.medium \\"
        echo "  --key-name YOUR_KEY_PAIR \\"
        echo "  --security-group-ids sg-xxxxx \\"
        echo "  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=email2kg-server}]'"
        ;;

    3)
        echo -e "${GREEN}Starting Docker Compose for local testing...${NC}"

        # Check if .env exists
        if [ ! -f .env ]; then
            echo -e "${YELLOW}Creating .env file from example...${NC}"
            if [ -f .env.example ]; then
                cp .env.example .env
                echo -e "${RED}Please edit .env file with your API keys before continuing!${NC}"
                exit 1
            else
                echo -e "${RED}.env.example not found. Please create .env file manually.${NC}"
                exit 1
            fi
        fi

        # Start services
        echo "Building and starting services..."
        docker-compose up --build -d

        echo ""
        echo -e "${GREEN}✓ Services started successfully!${NC}"
        echo ""
        echo "Access the application:"
        echo "  Frontend: http://localhost"
        echo "  Backend API: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo ""
        echo "View logs:"
        echo "  docker-compose logs -f"
        echo ""
        echo "Stop services:"
        echo "  docker-compose down"
        ;;

    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Deployment script completed!${NC}"

#!/bin/bash
set -ex

# Install Docker
dnf install -y docker
systemctl start docker
systemctl enable docker

# ECR login — registry URL derived from repo URL
ECR_REGISTRY="${ecr_registry}"
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin "$ECR_REGISTRY"

# Pull and run the application container
docker pull ${ecr_repo_url}:${docker_tag}

docker run -d --restart=unless-stopped \
  --name ${project} \
  -p 8081:8081 \
  -e S3_BUCKET=${s3_bucket} \
  -e AWS_DEFAULT_REGION=${aws_region} \
  -e READ_URL=${read_url} \
  ${ecr_repo_url}:${docker_tag}

echo "Deployment complete: ${ecr_repo_url}:${docker_tag}"

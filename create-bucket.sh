#!/bin/sh
set -e

echo "Creating MinIO bucket: ${S3_BUCKET_NAME}"

sleep 5

mc alias set myminio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

mc mb myminio/${S3_BUCKET_NAME} --ignore-existing

echo "Bucket created successfully!"
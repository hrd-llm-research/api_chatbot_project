# chatbot-api

## Installation

Install the LangChain CLI if you haven't yet

## Docker Setup

To run MinIO using Docker, execute the following command:

```sh
docker run -dp 9000:9000 -p 9001:9001 --name minio \
  -v /Users/phanith/Documents/data:/data \
  -e "MINIO_ROOT_USER=minioadmin"\
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  quay.io/minio/minio server /data --console-address ":9001"


Url : http://localhost:9001/
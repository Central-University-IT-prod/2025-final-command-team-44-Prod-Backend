import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiobotocore.session import get_session
from app.config import MINIO_ROOT_PASSWORD, MINIO_ROOT_USER, MINIO_URL
from botocore.exceptions import ClientError
from types_aiobotocore_s3.client import S3Client


@asynccontextmanager
async def get_client(bucket_name) -> AsyncGenerator["S3Client", None]:
    session = get_session()
    config = dict(
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
        endpoint_url=MINIO_URL,
    )

    async with session.create_client("s3", **config) as client:
        client: S3Client
        try:
            await client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                await client.create_bucket(Bucket=bucket_name)

                await client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(
                        {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Action": ["s3:GetObject"],
                                    "Effect": "Allow",
                                    "Principal": {"AWS": ["*"]},
                                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                                    "Sid": "",
                                }
                            ],
                        }
                    ),
                )

            raise

        yield client

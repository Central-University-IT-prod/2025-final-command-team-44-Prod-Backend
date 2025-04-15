from app.infra.s3.client import get_client
from botocore.exceptions import ClientError


class Storage:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name

    async def upload_file(self, file: bytes, filename: str):
        try:
            async with get_client(self.bucket_name) as client:
                await client.put_object(
                    Bucket=self.bucket_name, Key=filename, Body=file
                )
                print(f"File {filename} uploaded to {self.bucket_name}")
        except ClientError as e:
            print(f"Error uploading file: {e}")

    async def delete_file(self, filename: str):
        try:
            async with get_client(self.bucket_name) as client:
                await client.delete_object(Bucket=self.bucket_name, Key=filename)
                print(f"File {filename} deleted from {self.bucket_name}")
        except ClientError as e:
            print(f"Error deleting file: {e}")

    async def read_file(self, filename: str):
        try:
            async with get_client(self.bucket_name) as client:
                response = await client.get_object(
                    Bucket=self.bucket_name, Key=filename
                )
                return await response["Body"].read()
        except ClientError as e:
            print(f"Error downloading file: {e}")

    async def generate_url(self, filename: str):
        try:
            async with get_client(self.bucket_name) as client:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": filename},
                    ExpiresIn=3600,
                )
                return url
        except ClientError as e:
            print(f"Error getting file url: {e}")

    async def exists(self, filename: str):
        try:
            async with get_client(self.bucket_name) as client:
                await client.head_object(Bucket=self.bucket_name, Key=filename)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

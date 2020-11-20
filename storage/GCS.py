import os
import asyncio
import aiohttp
from gcloud.aio.storage import Storage
from errors.errors import GCSError



service_file_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
storage_client = Storage(service_file=service_file_path)
bucket_name = "memr-audiofiles"
bucket = storage_client.get_bucket(bucket_name)


async def upload_blob(audiofile_path, fileName):
    try:
        source_file_name = f"{audiofile_path}{fileName}"
        if not os.path.exists(source_file_name):
            raise GCSError("Source file does not exist.")

        await storage_client.upload_from_filename(bucket_name, fileName, source_file_name)
        print(f"File {source_file_name} uploaded to {fileName} in {bucket_name} bucket.")
    except GCSError:
        raise
    except:
        raise GCSError("Failed to store data in GCS.")


async def download_blob(storage_object_name, destination_file_name):
    try:
        await storage_client.download_to_filename(bucket_name, storage_object_name, destination_file_name)
        print(f"Blob {storage_object_name} downloaded to {destination_file_name}.")
    except Exception as e:
        raise GCSError("Failed to fetch data from GCS.", e)


async def delete_blob(storage_object_name):
    try:
        if await bucket.blob_exists(storage_object_name):
            await storage_client.delete(bucket_name, storage_object_name)
            print(f"Blob {storage_object_name} deleted.")
        else:
            raise GCSError(f"Failed to delete {storage_object_name}")
    except GCSError:
        raise
    except:
        raise GCSError("Failed to delete data from GCS.")


async def blob_exists(storage_object_name):
    try:
        if await bucket.blob_exists(storage_object_name):
            return True
        else:
            return False
    except Exception as e:
        raise GCSError("Failed to fetch data from GCS.", e)
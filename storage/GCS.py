import os
import io
import google.auth
import asyncio
from google.cloud import storage
from errors.errors import GCSError



credentials, project = google.auth.default()
bucket_name = "memr-audiofiles"
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)


def upload_blob(audiofile_path, fileName):
    try:
        source_file_name = f"{audiofile_path}{fileName}"

        if not os.path.exists(source_file_name):
            raise GCSError("Source file does not exist.")

        blob = bucket.blob(fileName)
        blob.upload_from_filename(source_file_name)

        print(f"File {source_file_name} uploaded to {fileName} in {bucket_name} bucket.")
    except GCSError:
        raise
    except:
        raise GCSError("Failed to store data in GCS.")


def download_blob(storage_object_name, destination_file_name):
    try:
        blob = bucket.blob(storage_object_name)
        blob.download_to_filename(destination_file_name)

        print(f"Blob {storage_object_name} downloaded to {destination_file_name}.")
    except:
        raise GCSError("Failed to fetch data from GCS.")


def delete_blob(storage_object_name):
    try:
        blob = bucket.blob(storage_object_name)
        blob.delete()

        if not blob.exists():
            print(f"Deleted {storage_object_name} blob.")
        else:
            raise GCSError(f"Could not delete {storage_object_name}")
    except GCSError:
        raise
    except:
        raise GCSError("Failed to delete data from GCS.")


def blob_exists(storage_object_name):
    try:
        blob = bucket.get_blob(storage_object_name)

        if blob:
            return True
        else:
            return False
    except:
        raise GCSError("Failed to fetch data from GCS.")
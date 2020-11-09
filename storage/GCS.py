import os
import io
import google.auth
import asyncio
from google.cloud import storage



credentials, project = google.auth.default()


def list_buckets():
    storage_client = storage.Client()
    buckets = storage_client.list_buckets()

    for bucket in buckets:
        print(bucket.name)


def upload_blob(source_file_name):
    bucket_name = "memr-audiofiles"
    source_file_name = source_file_name
    destination_blob_name = source_file_name.split("/")[-1]

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name} in {bucket_name} bucket.")


def download_blob(storage_object_name, destination_file_name):
    bucket_name = "memr-audiofiles"
    source_blob_name = storage_object_name

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")


def delete_blob(storage_object_name):
    bucket_name = "memr-audiofiles"
    source_blob_name = storage_object_name

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.delete()

    if not blob.exists():
        print(f"Deleted {source_blob_name} blob.")
    else:
        print(f"Could not delete {source_blob_name}")


def blob_exists(storage_object_name):
    bucket_name = "memr-audiofiles"
    
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(storage_object_name)

    if blob:
        return True
    else:
        return False
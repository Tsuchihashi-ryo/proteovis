import os
from google.cloud import storage
from io import BytesIO, StringIO

# --- GCS Client Initialization ---

def _get_gcs_client():
    """Initializes and returns a GCS storage client."""
    return storage.Client()

# --- Core GCS Operations ---

def upload_blob_from_string(bucket_name, string_data, destination_blob_name, content_type='text/plain'):
    """Uploads a string to the bucket."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(string_data, content_type=content_type)
    print(f"String data uploaded to gs://{bucket_name}/{destination_blob_name}.")

def upload_blob_from_file_object(bucket_name, file_obj, destination_blob_name):
    """Uploads a file object to the bucket."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Rewind the file object to the beginning
    file_obj.seek(0)
    blob.upload_from_file(file_obj)
    print(f"File object uploaded to gs://{bucket_name}/{destination_blob_name}.")

def download_blob_as_string(bucket_name, source_blob_name):
    """Downloads a blob from the bucket into a string."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    return blob.download_as_text()

def download_blob_to_file_object(bucket_name, source_blob_name):
    """Downloads a blob into an in-memory file object (BytesIO)."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    file_obj = BytesIO()
    blob.download_to_file(file_obj)
    file_obj.seek(0) # Rewind to the beginning
    return file_obj

def blob_exists(bucket_name, blob_name):
    """Checks if a blob exists."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.exists()

def list_blobs_with_prefix(bucket_name, prefix=None, delimiter=None):
    """Lists blobs in the bucket that begin with the prefix."""
    client = _get_gcs_client()
    blobs = client.list_blobs(bucket_name, prefix=prefix, delimiter=delimiter)
    return [blob.name for blob in blobs]

def list_directories(bucket_name, prefix):
    """
    Lists "subdirectories" in a given "directory" (prefix).
    This is achieved by using a delimiter.
    """
    client = _get_gcs_client()
    # Ensure the prefix ends with a slash to properly list subdirectories
    if prefix and not prefix.endswith('/'):
        prefix += '/'

    blobs = client.list_blobs(bucket_name, prefix=prefix, delimiter='/')

    # The "directories" are in the `prefixes` property of the iterator
    directories = []
    for page in blobs.pages:
        directories.extend(page.prefixes)

    # a.prefixes returns full paths like 'folder/subfolder/', strip the parent prefix and trailing slash
    return [d.replace(prefix, '').rstrip('/') for d in directories]


def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
    print(f"Blob {blob_name} deleted.")

def delete_folder(bucket_name, folder_prefix):
    """Deletes all blobs with the given folder prefix."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)

    # Ensure the prefix ends with a slash
    if not folder_prefix.endswith('/'):
        folder_prefix += '/'

    blobs = bucket.list_blobs(prefix=folder_prefix)
    for blob in blobs:
        blob.delete()
        print(f"Deleted {blob.name}")
    print(f"All files in folder {folder_prefix} have been deleted.")

# --- Pandas DataFrame Helpers ---

def dataframe_to_gcs_csv(df, bucket_name, destination_blob_name):
    """Writes a Pandas DataFrame to a CSV file on GCS."""
    csv_string = df.to_csv(index=False)
    upload_blob_from_string(bucket_name, csv_string, destination_blob_name, 'text/csv')

def gcs_csv_to_dataframe(bucket_name, source_blob_name):
    """Reads a CSV file from GCS into a Pandas DataFrame."""
    import pandas as pd
    csv_string = download_blob_as_string(bucket_name, source_blob_name)
    return pd.read_csv(StringIO(csv_string))

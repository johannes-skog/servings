from typing import List
import os
from azure.storage.blob import BlobServiceClient

class AzureBlobStorage(object):

    def __init__(self, connection_string: str, container_name: str):

        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

    def upload_file(self, filepath: str, blob_name: str) -> None:

        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )

        with open(filepath, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    def download_blob(self, blob: str, destination: str):

        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob
        )

        with open(destination, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())

    def get_latest_blobs(self) -> List[str]:

        container_client = self.blob_service_client.get_container_client(
            self.container_name
        )

        blobs = container_client.list_blobs()

        sorted_blobs = sorted(blobs, key=lambda x: x.last_modified, reverse=True)

        return [blob.name for blob in sorted_blobs]

    def upload_folder(self, folder_path: str, blob_folder_name: str) -> None:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Construct the blob name with the same folder structure
                relative_path = os.path.relpath(root, folder_path)
                if relative_path == '.':
                    blob_name = os.path.join(blob_folder_name, file)
                else:
                    blob_name = os.path.join(blob_folder_name, relative_path, file)
                # Remove any leading slashes
                blob_name = blob_name.lstrip('/')
                # Upload the file
                self.upload_file(file_path, blob_name)
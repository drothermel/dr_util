'''File adapted from ReFinED repo:
https://github.com/amazon-science/ReFinED/
    src/refined/resource_management/aws.py
'''

import boto3
import logging
import os

from typing import Optional
from botocore.handlers import disable_signing


class S3Manager:
    def __init__(self, boto3_session: Optional[boto3.Session] = None):
        """
        :param boto3_session: boto3 session (`boto3.Session`) optional,
        if not set will use default session
        High-level abstractions for working with S3.
        """
        if boto3_session:
            self._s3 = boto3_session.resource("s3")
        else:
            self._s3 = boto3.resource("s3")
        self._s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
        self._log = logging.getLogger("S3Manager")

    def download_file_if_needed(
        self,
        s3_bucket: str,
        s3_key: str,
        output_file_path: str,
    ) -> None:
        """
        Download a file from S3 and store at output_file_path if it has not already
        been downloaded. Only downloads file if a more recent timestamps exists on S3.
        :param s3_bucket: s3 bucket
        :param s3_key: s3 key
        :param output_file_path: output file path
        :param progress_bar: show progress bar
        :raises botocore.exceptions.ClientError when resource does not exist.
        """
        s3_obj = self._s3.Object(s3_bucket, s3_key)
        s3_obj_size = s3_obj.content_length
        s3_last_modified = int(s3_obj.last_modified.strftime("%s"))
        if (
            os.path.isfile(output_file_path)
            and int(os.stat(output_file_path).st_mtime) > s3_last_modified
        ):
            self._log.debug(f"File already downloaded: {output_file_path}.")
        else:
            self._log.debug(
                f"Downloading {output_file_path} file from S3 bucket: {s3_bucket}, key: {s3_key}"
            )
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            s3_obj.download_file(output_file_path)
            self._log.debug("Download complete.")

    def upload_bytes(self, bytes_to_upload: bytes, s3_bucket: str, s3_key: str) -> None:
        """
        Upload bytes to S3.
        :param bytes_to_upload: bytes
        :param s3_bucket: s3 bucket
        :param s3_key: s3 key
        """
        s3_bucket_resource = self._s3.Bucket(s3_bucket)
        s3_bucket_resource.put_object(Key=s3_key, Body=bytes_to_upload)

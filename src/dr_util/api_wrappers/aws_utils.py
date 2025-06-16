"""File adapted from ReFinED repo.

https://github.com/amazon-science/ReFinED/
    src/refined/resource_management/aws.py
"""

import logging
from pathlib import Path

import boto3
from botocore.handlers import disable_signing


class S3Manager:
    """High-level abstractions for working with S3."""
    def __init__(self, boto3_session: boto3.Session | None = None) -> None:
        """Initialize S3Manager.

        :param boto3_session: boto3 session (`boto3.Session`) optional,
        if not set will use default session
        High-level abstractions for working with S3.
        """
        self._log = logging.getLogger("S3Manager")
        if boto3_session:
            self._s3 = boto3_session.resource("s3")
            self._log.info(">> Using passed s3 session")
        else:
            self._s3 = boto3.resource("s3")
            self._log.info(">> Created new s3 session")
        self._s3.meta.client.meta.events.register("choose-signer.s3.*", disable_signing)

    def download_file_if_needed(
        self,
        s3_bucket: str,
        s3_key: str,
        output_file_path_str: str,
    ) -> None:
        """Download a file from S3 and store at output_file_path if needed.

        Only downloads file if a more recent timestamps exists on S3.
        :param s3_bucket: s3 bucket
        :param s3_key: s3 key
        :param output_file_path: output file path
        :param progress_bar: show progress bar
        :raises botocore.exceptions.ClientError when resource does not exist.
        """
        output_file_path = Path(output_file_path_str)
        s3_obj = self._s3.Object(s3_bucket, s3_key)
        s3_last_modified = int(s3_obj.last_modified.strftime("%s"))
        if (
            output_file_path.is_file()
            and int(output_file_path.stat().st_mtime) > s3_last_modified
        ):
            self._log.info(f">> File already downloaded: {output_file_path}.")
        else:
            self._log.info(
                f">> Downloading {output_file_path} file from"
                f"S3 bucket: {s3_bucket}, key: {s3_key}"
            )
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            s3_obj.download_file(str(output_file_path))
            self._log.info(">> Download complete.")

    def upload_bytes(self, bytes_to_upload: bytes, s3_bucket: str, s3_key: str) -> None:
        """Upload bytes to S3.

        :param bytes_to_upload: bytes
        :param s3_bucket: s3 bucket
        :param s3_key: s3 key
        """
        s3_bucket_resource = self._s3.Bucket(s3_bucket)
        s3_bucket_resource.put_object(Key=s3_key, Body=bytes_to_upload)
        self._log.info(f">> Upload to {s3_bucket} {s3_key} complete.")

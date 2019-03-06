import os
import shutil
import tempfile
import logging
from urllib.parse import urlparse

import boto3


LOGGER = logging.getLogger(__name__)


def is_s3_url(url):
    """Check whether the provided path is an s3 url.

    :param url: the S3 URL to check
    :return: `True` if the URL points to an S3 bucket key, `False` otherwise.
    """
    return urlparse(url).scheme == 's3'


def is_local_path(path):
    """Check whether the provided path is local.

    :param url: the local path to check
    :return: `True` if the path points to a local filesystem, `False`
        otherwise.
    """
    return urlparse(path).scheme in ['', 'file']


def upload_file(src_path, dst_url):
    """Upload a local file on S3.

    If the file already exists it is overwritten.

    :param src_path: Source local filesystem path
    :param dst_url: Destination S3 URL
    """
    parsed_url = urlparse(dst_url)
    dst_bucket = parsed_url.netloc
    dst_key = parsed_url.path[1:]

    client = boto3.client('s3')
    client.upload_file(src_path, dst_bucket, dst_key)


def download_file(src_url, dst_path):
    """Download a S3 URL to a local file.

    If the file already exists it is overwritten.

    :param src_url: Source S3 URL to download
    :param dst_path: Destination local path
    """
    parsed_url = urlparse(src_url)
    src_bucket = parsed_url.netloc
    src_key = parsed_url.path[1:]

    s3 = boto3.resource('s3')
    s3.Bucket(src_bucket).download_file(src_key, dst_path)

def _s3_path_exists(path):
    """Return if an S3 path exists.

    Directory is not a S3 concept so only check if a file exists.

    :param path: Path or s3 URL (Example: s3://xxx/y.h5 or /data/y.h5)
    :return: boolean indicating if path exists
    """
    client = boto3.client('s3')
    url = urlparse(path)
    result = client.list_objects(
        Bucket=url.netloc,
        Prefix=url.path.lstrip('/'))

    # If result has contents, then file exists on S3
    return 'Contents' in result


def remove_path(path):
    """Remove a path to a file.

    :param path: Path or s3 URL (Example: s3://xxx/y.h5 or /data/y.h5)
    """
    if is_s3_url(path):
        client = boto3.client('s3')
        url = urlparse(path)
        client.delete_object(Bucket=url.netloc, Key=url.path[1:])

    if is_local_path(path):
        os.remove(path)


def path_exists(path):
    """Return if a path already exists (s3 or directory path).

    :param path: Path or s3 URL (Example: s3://xxx/y.h5 or /data/y.h5)
    :return: boolean indicating if path exists
    """
    if is_s3_url(path):
        return _s3_path_exists(path)

    if is_local_path(path):
        return os.path.exists(path)

    raise ValueError("Invalid path %s" % path)


def path_is_file(path):
    """Return if a path already exists (s3 or directory path).

    :param path: Path or s3 URL (Example: s3://xxx/y.h5 or /data/y.h5)
    :return: boolean indicating if path exists
    """
    if is_s3_url(path):
        return _s3_path_exists(path)

    if is_local_path(path):
        return os.path.isfile(path)

    raise ValueError("Invalid path %s" % path)


def path_is_readable_file(path):
    """Return if a path already exists (s3 or directory path) and is readable.

    :param path: Path or s3 URL (Example: s3://xxx/y.h5 or /data/y.h5)
    :return: boolean indicating if path exists
    """
    if not path_is_file(path):
        return False

    if is_s3_url(path):
        # TODO: check if file is readable
        return True

    if is_local_path(path):
        try:
            with open(path, mode='r'):
                return True
        except PermissionError:
            return False

    raise ValueError("Invalid path %s" % path)


def create_writable_directory(path):
    """Create a directory if it does not exist

    Does nothing if s3 URL is provided.

    :param path: Path or s3 URL (Example: s3://xxx/ or /data/dir/)
    """
    if not is_local_path(path):
        # Directories only make sense locally
        # TODO: Check write permission on S3 path
        return

    if not os.path.exists(path):
        os.makedirs(path)
    assert os.access(path, os.W_OK), \
        'No write access to output directory: %s' % path


class LocalFile():
    """Context manager to get a local file indifferently from local or S3."""

    def __init__(self, path, upload=False):
        """

        :param path: Path or s3 URL (Example: s3://xxx/y.h5 or /data/y.h5)
        :param upload: boolean used to upload local file back to S3 at the
                       end. Default: False
        """
        self.tmpdir = None
        self.path = path
        self.filename = os.path.realpath(path)
        self.upload = False

        if is_s3_url(path):
            basename = path.split('/')[-1]
            # Create a safe (user only readable/writable) temporary directory
            self.upload = upload
            self.tmpdir = tempfile.mkdtemp()
            self.filename = os.path.join(self.tmpdir, basename)

            if _s3_path_exists(path):
                LOGGER.info("Downloading %s to %s", self.path, self.filename)
                download_file(self.path, self.filename)

    def __enter__(self):
        return self.filename

    def __exit__(self, *args):
        if self.tmpdir:
            if self.upload:
                # Upload the file at the end
                LOGGER.info("Uploading %s to %s", self.filename, self.path)
                upload_file(self.filename, self.path)

            # Remove temporary directory
            shutil.rmtree(self.tmpdir)


def disable_s3_verbose_logging():
    """Disable S3 verbose logging."""
    # Suppress following two logs logged at INFO level
    #   - "Starting new HTTPS connection"
    #   - "Found credentials in shared credentials file"
    logging.getLogger('botocore').setLevel(logging.WARNING)

    # Suppress other DEBUG logs from third-party library
    logging.getLogger('s3transfer').setLevel(logging.INFO)
    logging.getLogger('boto3').setLevel(logging.INFO)

import os
import tempfile
from contextlib import contextmanager

import boto3

from bot.env import env


class Storage(object):
    def __init__(self):
        self.session = boto3.resource(
            service_name='s3',
            region_name=env['S3_REGION'],
            aws_access_key_id=env['AWS_KEY'],
            aws_secret_access_key=env['AWS_SECRET']
        )
        self.bucket = self.session.Bucket(env['S3_BUCKET'])

    @contextmanager
    def get(self, path):
        filename, file_extension = os.path.splitext(path)
        temporary_file = tempfile.NamedTemporaryFile(suffix=file_extension)
        self.bucket.download_file(path, temporary_file.name)
        with open(temporary_file.name, 'rb') as file:
            try:
                yield file
            finally:
                temporary_file.close()

storage = Storage()

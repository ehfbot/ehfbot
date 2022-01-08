import os
import sys
from collections import UserDict

from dotenv import dotenv_values


class Env(UserDict):
    REQUIRED_KEYS = ('DISCORD_TOKEN', 'S3_REGION', 'S3_BUCKET', 'AWS_KEY', 'AWS_SECRET', 'DATABASE_PROVIDER', 'DATABASE_HOST', 'DATABASE_USER', 'DATABASE_PASSWORD', 'DATABASE_NAME', 'GUILD_IDS')

    def __init__(self):
        self.data = {}
        for key in self.REQUIRED_KEYS:
            value = os.getenv(key) # used in heroku/production
            if value:
                self.data[key] = value

        self.data.update(dotenv_values(".env")) # usually only used in development

        self.warn_about_missing_keys()

    def warn_about_missing_keys(self):
        missing_keys = set(self.REQUIRED_KEYS) - set(self.data)
        if missing_keys:
            sys.exit(f"{missing_keys} must be set in environment")

env = Env()

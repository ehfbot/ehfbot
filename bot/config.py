from collections import UserDict

import yaml

from bot.env import env


class Config(UserDict):
    def __init__(self):
        self.data = self.load_config()
        self.data.update(self.load_env(env))

    def load_config(self):
        data = {}
        with open('config/app.yml', 'r') as file:
            data = yaml.load(file.read(), Loader=yaml.FullLoader)
        return data

    def load_env(self, env):
        return ({
            'discord': {
                'token': env['DISCORD_TOKEN'],
            },
        })

config = Config()

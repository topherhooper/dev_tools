import yaml
import typing


def get_credentials() -> typing.Dict:
    credentials_yaml = "/workspace/dev_tools/credentials/discord.yaml"

    with open(credentials_yaml, "r") as f:
        config = yaml.safe_load(f)
    return config

def get_discord_token():
    credentials = get_credentials()
    return credentials["shared_bot"]["discord"]


def get_openai_token():
    credentials = get_credentials()
    return credentials["shared_bot"]["openai"]
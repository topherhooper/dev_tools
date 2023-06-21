import yaml
import typing


def get_credentials() -> typing.Dict:
    credentials_yaml = "/workspace/dev_tools/credentials/discord.yaml"

    with open(credentials_yaml, "r") as f:
        config = yaml.safe_load(f)
    return config

# This example requires the 'message_content' intent.
from credentials import get_credentials
from chatgpt import Brain
import typing
from brain_bot import BrainBot, DEFAULT_INTENTS


def aetheris():
    credentials = get_credentials()
    aetheris_token = credentials["Aetheris"]["discord"]
    aetheris_brain = Brain(prompt_name="aetheris")
    aetheris_client = BrainBot(brain=aetheris_brain, intents=DEFAULT_INTENTS)
    aetheris_client.run(aetheris_token)


if __name__ == "__main__":
    aetheris()

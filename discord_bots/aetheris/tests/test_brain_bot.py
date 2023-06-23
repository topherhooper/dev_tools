import unittest

# This example requires the 'message_content' intent.
from credentials import get_discord_token, get_openai_token
from chatgpt import Brain
import typing
from brain_bot import BrainBot, DEFAULT_INTENTS


class TestBrainBot(unittest.TestCase):
    def test_integrations(self, *args):
        discord_token = get_discord_token()
        brain_token = get_openai_token()
        brain = Brain(api_key=brain_token)
        brain_bot = BrainBot(brain=brain, intents=DEFAULT_INTENTS)
        brain.get_brain_response(message="test")
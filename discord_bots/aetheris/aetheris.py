# This example requires the 'message_content' intent.
from credentials import get_discord_token, get_openai_token
from chatgpt import Brain
import typing
from brain_bot import BrainBot, DEFAULT_INTENTS


def aetheris():
    bot_name = "aetheris"
    discord_token = get_discord_token()
    brain_token = get_openai_token()
    brain = Brain(prompt_names=[bot_name, "eldoria"], api_key=brain_token)
    brain_bot = BrainBot(brain=brain, intents=DEFAULT_INTENTS)
    brain_bot.run(discord_token)


if __name__ == "__main__":
    aetheris()

# This example requires the 'message_content' intent.
from credentials import get_discord_token, get_openai_token
from chatgpt import Brain
import typing
from brain_bot import BrainBot, DEFAULT_INTENTS


class Aetheris:
    name = "aetheris"
    description = "Aetheris is an old professor. They are funny and jolly, and love telling a story about the world's history and local folk tales."

    def __init__(
        self,
    ):
        self.bot_name = self.name
        self.discord_token = get_discord_token()
        self.brain_token = get_openai_token()
        self.brain = Brain(
            prompt_names=[self.name, "eldoria"], api_key=self.brain_token
        )
        self.brain_bot = BrainBot(brain=self.brain, intents=DEFAULT_INTENTS)

    def run(self):
        self.brain_bot.run(self.discord_token)


def aetheris():
    brain_bot = Aetheris()
    brain_bot.run()


if __name__ == "__main__":
    aetheris()

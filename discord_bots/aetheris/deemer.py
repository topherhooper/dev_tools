from credentials import get_discord_token, get_openai_token
from chatgpt import Brain
from brain_bot import BrainBot, DEFAULT_INTENTS


class Deemer:
    name = "deemer"
    description = "Deemer is the Game Master's helper!"

    def __init__(self):
        self.discord_token = get_discord_token()
        self.brain_token = get_openai_token()
        self.brain = Brain(
            prompt_names=[self.name, "eldoria"], api_key=self.brain_token
        )
        self.brain_bot = BrainBot(brain=self.brain, intents=DEFAULT_INTENTS)

    def run(self):
        self.brain_bot.run(self.discord_token)


def deemer():
    brain_bot = Deemer()
    brain_bot.run()


if __name__ == "__main__":
    deemer()

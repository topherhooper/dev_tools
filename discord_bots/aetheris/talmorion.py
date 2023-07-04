from credentials import get_discord_token, get_openai_token
from chatgpt import Brain
from brain_bot import BrainBot, DEFAULT_INTENTS


class Talmorion:
    name = "talmorion"
    description = "Lord Talmorion Ravenshield is a benevolent lich lord. They are lord over a small fiefdom. They partner with their subjects to provide donations of blood to power an army of undead to protect the community."

    def __init__(self):
        self.discord_token = get_discord_token()
        self.brain_token = get_openai_token()
        self.brain = Brain(
            prompt_names=[self.name, "eldoria"], api_key=self.brain_token
        )
        self.brain_bot = BrainBot(brain=self.brain, intents=DEFAULT_INTENTS)

    def run(self):
        self.brain_bot.run(self.discord_token)


def talmorion():
    brain_bot = Talmorion()
    brain_bot.run()


if __name__ == "__main__":
    talmorion()

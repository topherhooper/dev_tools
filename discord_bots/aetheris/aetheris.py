# This example requires the 'message_content' intent.
import discord
from credentials import get_credentials
from chatgpt import Brain
import typing


intents = discord.Intents.default()
intents.message_content = True
aetheris_brain = Brain(
    system="Your name is Aetheris. You are a historian NPC within a fantasy world."
)

allowed_channel_ids = [799792721404887050]  # play-with-bots,


class DiscordBot(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Check if the message is sent in an allowed channel
        if message.channel.id not in allowed_channel_ids:
            return
        if self.user.mentioned_in(message) or message.content.startswith(
            f"{self.user.name} "
        ):
            print(f"Message from {message.author}: {message.content}")
            await self.ask_aetheris(message)

    async def ask_aetheris(self, message: str):
        brain_response = aetheris_brain.get_brain_response(message=message.content)
        await message.channel.send(brain_response)

    async def ping(self, message):
        await message.channel.send("Pong!")

    async def greet(self, message):
        author = message.author
        await message.channel.send(f"Hello, {author.mention}!")


def main():
    credentials = get_credentials()
    aetheris_token = credentials["Aetheris"]["discord"]
    aetheris_client = DiscordBot(intents=intents)
    aetheris_client.run(aetheris_token)


if __name__ == "__main__":
    main()

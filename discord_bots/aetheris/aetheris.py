# This example requires the 'message_content' intent.
import discord
from credentials import get_credentials


intents = discord.Intents.default()
intents.message_content = True


class Aetheris(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    async def on_message(self, message):
        if message.author == self.user:
            return
        print(f"Message from {message.author}: {message.content}")
        await self.greet(message)
        await self.ping(message)

    async def ping(self, message):
        await message.channel.send("Pong!")

    async def greet(self, message):
        author = message.author
        await message.channel.send(f"Hello, {author.mention}!")


def main():
    credentials = get_credentials()
    aetheris_token = credentials["Aetheris"]["token"]
    client = Aetheris(intents=intents)
    client.run(aetheris_token)


if __name__ == "__main__":
    main()

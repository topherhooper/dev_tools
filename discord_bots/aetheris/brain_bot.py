import discord
from credentials import get_credentials
from chatgpt import Brain
import typing
from collections import defaultdict
from datetime import datetime, timedelta


DEFAULT_INTENTS = discord.Intents.default()
DEFAULT_INTENTS.message_content = True
allowed_channel_ids = [799792721404887050]  # play-with-bots,

# Define the rate limit parameters
RATE_LIMIT = 5  # min delta between message

# Define a dictionary to store user timestamps
user_timestamps = {}
user_testing_patience = defaultdict(int)
MAX_WARNINGS = 3


class BrainBot(discord.Client):
    def __init__(self, brain: Brain, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brain = brain

    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    def check_user_rate(self, message):
        # Get the current timestamp
        current_timestamp = datetime.now()

        # Check if the user is already in the timestamp dictionary
        if message.author.id in user_timestamps:
            # Get the timestamp of the user's last message
            last_timestamp = user_timestamps[message.author.id]

            # Calculate the time elapsed since the last message
            elapsed_time = current_timestamp - last_timestamp

            # Check if the cooldown period has not expired
            if elapsed_time < timedelta(seconds=RATE_LIMIT):
                return False

        # Update the user's timestamp in the dictionary
        user_timestamps[message.author.id] = current_timestamp
        return True

    async def message_abuse(self, message):
        # Inform the user about the cooldown period
        user_testing_patience[message.author.id] += 1
        tries_with_user = user_testing_patience[message.author.id]

        # send a personalized message.
        user_name = message.author.name
        please_wait_message = f"{user_name}! Please be patient! I'm getting to that. Wait a bit before sending another message."
        patience_message = f"You've gotten this warning {tries_with_user} times. You get 3 warnings before you're ignored."
        await message.channel.send(f"{please_wait_message} {patience_message}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        tries_with_user = user_testing_patience[message.author.id]
        if tries_with_user >= MAX_WARNINGS:
            return
        # Check if the message is sent in an allowed channel or in a DM
        if (
            message.channel.id not in allowed_channel_ids
            and message.channel.type != discord.ChannelType.private
        ):
            return

        if (
            self.user.mentioned_in(message)
            or message.content.startswith(f"{self.user.name}")
            or (message.channel.type == discord.ChannelType.private)
        ):
            check_user_abuse = self.check_user_rate(message)
            if not check_user_abuse:
                await self.message_abuse(message)
                return
            await self.ask_brain(message)

    async def ask_brain(self, message: str):
        brain_response = self.brain.get_brain_response(message=message.content)
        await message.channel.send(brain_response)

    async def ping(self, message):
        await message.channel.send("Pong!")

    async def greet(self, message):
        author = message.author
        await message.channel.send(f"Hello, {author.mention}!")

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
                return True

        # Update the user's timestamp in the dictionary
        user_timestamps[message.author.id] = current_timestamp
        return False

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
        is_dm = bool(message.channel.type == discord.ChannelType.private)
        is_allowed_channel = bool(message.channel.id in allowed_channel_ids)
        is_bot_addressed = bool(self.user.mentioned_in(message) or is_dm)

        if not is_allowed_channel and not is_bot_addressed:
            return

        if (
            self.user.mentioned_in(message)
            or message.content.startswith(f"{self.user.name}")
            or (message.channel.type == discord.ChannelType.private)
        ):
            print(f"Replying to {message.author.name}")
            is_abusive_user = self.check_user_rate(message)
            if is_abusive_user:
                await self.message_abuse(message)
                return
            await self.ask_brain(message)

    async def ask_brain(self, message: str):
        brain_response = self.brain.get_brain_response(message=message.content)
        await message.channel.send(brain_response)

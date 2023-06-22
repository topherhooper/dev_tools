from collections import namedtuple
import openai
import typing
from credentials import get_credentials

BrainMessage = namedtuple("BrainMessage", "user message")

# count tokens:
# https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

ChatGPTModel: str = "gpt-3.5-turbo"
# ChatGPTModel: str = "text-davinci-003"


def num_tokens_from_string(string: str, model: str = ChatGPTModel) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(ChatGPTModel)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class ConversationHistory:
    def __init__(self, system: typing.Optional[str] = None):
        self.conversation_history = []
        self.set_system(system=system)

    def user_says(self, message):
        self.conversation_history.append(
            {"role": "user", "content": message},
        )
        print(message)

    def set_system(self, system: typing.Optional[str] = None):
        if system is None:
            system = "You are a helpful assistant."
        # Append the new message to the conversation history
        self.conversation_history.append(
            {"role": "system", "content": system},
        )

    def reponse_says(self, message):
        self.conversation_history.append(
            {"role": "assistant", "content": message},
        )

    def get(self):
        return self.conversation_history


class Brain:
    def __init__(self, system: str):
        self.conversation_history = ConversationHistory(system=system)
        openai.api_key = get_credentials()["Aetheris"]["openai"]

    def get_brain_response(self, message):
        self.conversation_history.user_says(message=message)
        # Generate response using ChatGPT
        completion = openai.ChatCompletion.create(
            model=ChatGPTModel, messages=self.conversation_history.get()
        )
        response = completion.choices[0].message.content
        print(response)

        self.conversation_history.reponse_says(response)
        return response

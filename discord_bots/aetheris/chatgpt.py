from collections import namedtuple
import openai
import typing
import json
from credentials import get_credentials


def load_prompts(prompt_name: str):
    prompt_filepath = (
        f"/workspace/dev_tools/discord_bots/aetheris/prompts/{prompt_name}.json"
    )
    print(prompt_filepath)
    with open(prompt_filepath, "r") as f:
        prompts = json.load(f)
    return prompts


BrainMessage = namedtuple("BrainMessage", "user message")

# count tokens:
# https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

ChatGPTModel: str = "gpt-3.5-turbo"


def num_tokens_from_string(string: str, model: str = ChatGPTModel) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(ChatGPTModel)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class ConversationHistory:
    def __init__(self, prompt_name: str = None):
        seed_prompts = load_prompts(prompt_name)
        self.conversation_history = []
        self.set_system(seed_prompts=seed_prompts)

    def user_says(self, message):
        self.conversation_history.append(
            {"role": "user", "content": message},
        )
        print(message)

    def set_system(
        self, seed_prompts: typing.Optional[typing.List[typing.Dict[str, str]]] = None
    ):
        if seed_prompts is None:
            seed_prompts = (
                {"role": "system", "content": "You are a helpful assistant."},
            )
        self.conversation_history = seed_prompts

    def reponse_says(self, message):
        self.conversation_history.append(
            {"role": "assistant", "content": message},
        )

    def get(self):
        return self.conversation_history


class Brain:
    def __init__(self, prompt_name: str):
        self.conversation_history = ConversationHistory(prompt_name=prompt_name)
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

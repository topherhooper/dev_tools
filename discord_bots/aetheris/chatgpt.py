import openai
import namedtuple

BrainMessage = namedtuple("BrainMessage", "user message")

"""

        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
"""


class ConversationHistory:
    def __init__(self, system=None):
        self.conversation_history = []
        self.set_system(system=system)

    def user_says(self, message):
        self.conversation_history.append(
            {"role": "user", "content": message},
        )

    def set_system(self, system):
        if not system:
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
    def __init__(self):
        self.conversation_history = ConversationHistory()

    def get_brain_response(self):
        # Generate response using ChatGPT
        response = openai.Completion.create(
            engine="text-davinci-003",  # Choose the appropriate ChatGPT model
            prompt=self.conversation_history.get(),
            max_tokens=50,  # Adjust the max tokens as needed
        )


openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {
            "role": "assistant",
            "content": "The Los Angeles Dodgers won the World Series in 2020.",
        },
        {"role": "user", "content": "Where was it played?"},
    ],
)
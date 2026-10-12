from collections import deque


class ConversationManager:

    def __init__(self, max_turns=10):

        self.history = deque(
            maxlen=max_turns
        )

    def add_user(self, text):

        self.history.append({
            "role": "user",
            "content": text
        })

    def add_assistant(self, text):

        self.history.append({
            "role": "assistant",
            "content": text
        })

    def get_history(self):

        return list(self.history)

    def get_previous_history(self):
        """Return conversation context before the current user turn."""
        history = list(self.history)
        return history[:-1] if history else []

    def build_context(self):

        if not self.history:
            return ""

        lines = []

        for message in self.history:

            role = message["role"].capitalize()

            content = message["content"]

            lines.append(
                f"{role}: {content}"
            )

        return "\n".join(lines)

    def clear(self):

        self.history.clear()


if __name__ == "__main__":

    print()
    print("==============================")
    print("     US AI CONVERSATION TEST")
    print("==============================")

    conversation = ConversationManager()

    conversation.add_user(
        "Do you know about the history of Pakistan?"
    )

    conversation.add_assistant(
        "Yes. Pakistan was established in 1947."
    )

    conversation.add_user(
        "Tell me more about it."
    )

    print()
    print("Conversation:")
    print("------------------------------")

    print(
        conversation.build_context()
    )

    print()
    print("==============================")
    print("      TEST COMPLETE")
    print("==============================")

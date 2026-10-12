import unittest

from brain.brain import format_spoken_answer
from brain.conversation import ConversationManager


class ConversationAndBrainTests(unittest.TestCase):
    def test_previous_history_excludes_current_turn(self):
        conversation = ConversationManager()
        conversation.add_user("Earlier question")
        conversation.add_assistant("Earlier answer")
        conversation.add_user("Current question")

        self.assertEqual(
            conversation.get_previous_history(),
            [
                {"role": "user", "content": "Earlier question"},
                {"role": "assistant", "content": "Earlier answer"},
            ],
        )

    def test_spoken_answer_is_compact(self):
        result = format_spoken_answer(
            "**First sentence.** Second sentence. Third sentence.",
            max_sentences=2,
            max_chars=200,
        )

        self.assertEqual(result, "First sentence. Second sentence.")


if __name__ == "__main__":
    unittest.main()

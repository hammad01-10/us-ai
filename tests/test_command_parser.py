import unittest

from brain.command_parser import parse_command


class CommandParserTests(unittest.TestCase):
    def test_system_control(self):
        self.assertEqual(
            parse_command("what time is it"),
            {"intent": "system_control", "action": "get_time"},
        )

    def test_memory_command(self):
        self.assertEqual(
            parse_command("my name is Alex"),
            {"intent": "memory", "action": "set_name", "name": "Alex"},
        )

    def test_direct_website(self):
        self.assertEqual(
            parse_command("open google.com"),
            {"intent": "open_website", "url": "https://google.com"},
        )

    def test_general_question(self):
        self.assertEqual(
            parse_command("what is the capital of Pakistan"),
            {"intent": "ask_ai", "query": "what is the capital of Pakistan"},
        )

    def test_long_browser_media_resume_request(self):
        self.assertEqual(
            parse_command("play the song already playing on Google's tab but paused"),
            {"intent": "system_control", "action": "media_play_pause"},
        )

    def test_long_browser_media_pause_request(self):
        self.assertEqual(
            parse_command("pause the song playing on Google's tab"),
            {"intent": "system_control", "action": "media_play_pause"},
        )


if __name__ == "__main__":
    unittest.main()

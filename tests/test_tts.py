import unittest

import numpy as np

from voice.tts import _finish_audio, _prepare_speech_text


class TtsPolishTests(unittest.TestCase):
    def test_prepare_speech_text_removes_visual_formatting(self):
        result = _prepare_speech_text("**Ready** — *launching* & checking")
        self.assertEqual(result, "Ready — launching and checking")

    def test_finish_audio_limits_peak_and_fades_edges(self):
        audio = np.ones(1600, dtype=np.float32)
        result = _finish_audio(audio, 16000)
        self.assertLessEqual(float(np.max(np.abs(result))), 0.84)
        self.assertEqual(float(result[0]), 0.0)
        self.assertEqual(float(result[-1]), 0.0)


if __name__ == "__main__":
    unittest.main()

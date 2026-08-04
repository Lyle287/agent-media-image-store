"""Focused tests for deterministic identity and local persistence."""

import base64
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from media_image_store import MediaImageStore, request_id_for


class FakeImages:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, **kwargs: object) -> SimpleNamespace:
        self.calls += 1
        image = SimpleNamespace(b64_json=base64.b64encode(b"png-bytes").decode())
        return SimpleNamespace(data=[image])


class MediaImageStoreTest(unittest.TestCase):
    @patch.dict(os.environ, {"INFRAI_API_KEY": "test-key"})
    @patch("media_image_store.OpenAI")
    def test_same_request_reuses_saved_image(self, openai: object) -> None:
        images = FakeImages()
        openai.return_value = SimpleNamespace(images=images)

        with tempfile.TemporaryDirectory() as directory:
            store = MediaImageStore(Path(directory))
            first = store.generate("A glass data center", "image-run-42")
            second = store.generate("A glass data center", "image-run-42")

            self.assertEqual(first, second)
            self.assertEqual(first.read_bytes(), b"png-bytes")
            self.assertEqual(images.calls, 1)

    def test_request_id_is_stable(self) -> None:
        self.assertEqual(request_id_for("frame"), request_id_for("frame"))
        self.assertNotEqual(request_id_for("frame"), request_id_for("scene"))


if __name__ == "__main__":
    unittest.main()

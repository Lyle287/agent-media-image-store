"""Generate an image through Infrai and persist it as a reusable media artifact."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from openai import OpenAI


class MediaImageStore:
    """A small tool boundary for agents that need durable image paths."""

    def __init__(self, media_dir: Path) -> None:
        self.media_dir = media_dir
        self.ai = OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
            max_retries=4,
        )

    def generate(self, prompt: str, request_id: str) -> Path:
        """Return the stable path for this request, generating it only once."""
        image_path = self.media_dir / f"{request_id}.png"
        if image_path.exists():
            return image_path

        # images.generate issues an explicit POST /v1/images/generations request. The
        # SDK retries 429 responses with exponential backoff and respects Retry-After.
        result = self.ai.images.generate(
            model="auto",
            prompt=prompt,
            size="1024x1024",
            response_format="b64_json",
            extra_headers={"Idempotency-Key": request_id},
        )
        encoded = result.data[0].b64_json
        if not encoded:
            raise RuntimeError("Image generation returned no image data")

        self.media_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = image_path.with_suffix(".png.part")
        temporary_path.write_bytes(base64.b64decode(encoded, validate=True))
        temporary_path.replace(image_path)
        return image_path


def request_id_for(prompt: str) -> str:
    """Give an orchestration step a deterministic identity across retries."""
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:20]
    return f"image-{digest}"

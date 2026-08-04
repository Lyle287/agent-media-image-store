"""Generate one media image, then host the media directory over HTTP."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from media_image_store import MediaImageStore, request_id_for


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Description of the image to generate")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--media-dir", type=Path, default=Path("generated-media"))
    args = parser.parse_args()

    request_id = request_id_for(args.prompt)
    image_path = MediaImageStore(args.media_dir).generate(args.prompt, request_id)

    handler = partial(SimpleHTTPRequestHandler, directory=str(args.media_dir))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Generated: {image_path}")
    print(f"Serving:   http://127.0.0.1:{args.port}/{image_path.name}")
    server.serve_forever()


if __name__ == "__main__":
    main()

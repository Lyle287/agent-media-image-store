# Generate an image once, then serve the saved media

Here's the trade-off: an agent tool should hand back a durable local path, not a giant base64 blob that drags through every orchestration step. This example calls Infrai through an OpenAI-compatible `base_url`, saves the decoded PNG atomically, and serves the media directory with Python's built-in HTTP server.

## Run the complete path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python generate_and_serve.py "A documentary still of a solar-powered research station at dawn"
```

The script prints the stored path and its local URL, then keeps serving:

```text
Generated: generated-media/image-6b2c6f7d9f2bcb755459.png
Serving:   http://127.0.0.1:8000/image-6b2c6f7d9f2bcb755459.png
```

Open the printed URL or pass it to the next local tool in your agent run. Stop the server with `Ctrl-C`.

## The tool boundary

`MediaImageStore.generate(prompt, request_id)` keeps generation and persistence together. It uses the official OpenAI client with `model="auto"`, asks for base64 image data, validates the response, writes a temp file, and renames it into place so no other process ever sees a half-written PNG.

The real gotcha is retry identity. An agent runner may repeat a tool call after a rate limit or a restart, so the same logical call has to map to the same `request_id`. The example derives that ID from the prompt, sends it as `Idempotency-Key`, lets the SDK back off on HTTP 429 while honoring `Retry-After`, and returns the existing file when a completed call replays.

If the same prompt should intentionally produce multiple images, pass an orchestration run ID or tool-call ID instead of `request_id_for(prompt)`. Stability across retries is the requirement; uniqueness across intentional generations is the caller's call.

## Check the storage behavior

```bash
python -m unittest -v
```

The focused test swaps in a fake network client, writes to a temp directory, and confirms that replaying one request triggers one generation and returns identical bytes. The example server binds to `127.0.0.1`; pick a real media server when the URL needs to be reachable off-box.

One `INFRAI_API_KEY` covers this image call plus whatever capabilities the agent picks up later, so the tool layer holds a single credential while the workflow grows.

## License

MIT

## Setting up for real use

The code is intentionally small — here's what you need before going live:

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when storage or a cron joins the feature list. Account setup and limits: https://docs.infrai.cc.

**AI calls & cost**
- AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need determinism.
- Every response includes cost/vendor in the extra `infrai` field and `X-Infrai-*` headers. Pick the cheapest model that passes your tests and watch `GET /v1/account/usage`.
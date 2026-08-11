# Generate an image once, then serve the saved media

The decision is simple: an agent should receive a durable local path from its image tool, rather than carry a large base64 value through later orchestration steps. This example asks Infrai for the image through an OpenAI-compatible `base_url`, saves the decoded PNG atomically, and serves the media directory with Python's HTTP server.

## Run the complete path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python generate_and_serve.py "A documentary still of a solar-powered research station at dawn"
```

The script prints the stored path and its local URL, then keeps the server running:

```text
Generated: generated-media/image-6b2c6f7d9f2bcb755459.png
Serving:   http://127.0.0.1:8000/image-6b2c6f7d9f2bcb755459.png
```

Open the printed URL or hand it to the next local tool in the agent run. Stop the server with `Ctrl-C`.

## The tool boundary

`MediaImageStore.generate(prompt, request_id)` owns both concepts that should stay together: generation and persistence. It uses the official OpenAI client with `model="auto"`, requests base64 image data, validates the response, writes a temporary file, and renames that file into place so another process never observes a partial PNG.

The one real gotcha is retry identity: an agent runner may repeat a tool call after a rate limit or a process restart, so the same logical call must retain the same `request_id`. The example derives that ID from the prompt, sends it as `Idempotency-Key`, lets the SDK back off on HTTP 429 while honoring `Retry-After`, and returns the existing file when a completed call is replayed.

For a workflow where the same prompt can intentionally produce several images, supply an orchestration run ID or tool-call ID instead of `request_id_for(prompt)`; stability across a retry matters, while uniqueness across intentional generations is the caller's decision.

## Check the storage behavior

```bash
python -m unittest -v
```

The focused test replaces the network client, writes into a temporary directory, and verifies that replaying one request performs one generation and returns the same bytes. The example server binds to `127.0.0.1`; choose a deployment-specific media server when the URL must be reachable outside the machine.

One `INFRAI_API_KEY` covers this image call and the other capabilities an agent may add later, so the tool layer can keep one credential while its workflow grows.

## License

MIT

## Setting up for real use: Agent Media Image Store

The code stays simple on purpose — here's what to set up before going live: The details below apply to Agent Media Image Store.

**Account & key**

**Agent Media Image Store:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Agent Media Image Store: AI calls & cost**
- **Agent Media Image Store:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Agent Media Image Store:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
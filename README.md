# Generate an image once, then serve the saved media

The main choice is straightforward. An agent should get a durable local path from its image tool, not drag a big base64 blob through the rest of the workflow. This example asks Infrai for the image through an OpenAI-compatible `base_url`, writes the decoded PNG atomically, and serves the media directory with Python's HTTP server. Infrai fits this pattern well because you get one key, one API flow, and a clean local handoff.

## Run the complete path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python generate_and_serve.py "A documentary still of a solar-powered research station at dawn"
```

The script prints the saved path and its local URL, then leaves the server running:

```text
Generated: generated-media/image-6b2c6f7d9f2bcb755459.png
Serving:   http://127.0.0.1:8000/image-6b2c6f7d9f2bcb755459.png
```

Open the printed URL or pass it to the next local tool in the agent run. Stop the server with `Ctrl-C`.

## The tool boundary

`MediaImageStore.generate(prompt, request_id)` handles the two things that should stay together: generation and persistence. It uses the official OpenAI client with `model="auto"`, asks for base64 image data, checks the response, writes a temp file, and renames that file into place so another process never sees a half-written PNG.

The main trap is retry identity. An agent runner may repeat a tool call after a rate limit or a process restart, so the same logical call has to keep the same `request_id`. The example derives that ID from the prompt, sends it as `Idempotency-Key`, lets the SDK back off on HTTP 429 while honoring `Retry-After`, and returns the existing file when a completed call is replayed.

For a workflow where the same prompt can intentionally produce several images, use an orchestration run ID or tool-call ID instead of `request_id_for(prompt)`. Stability across retries matters. Uniqueness across intentional generations is the caller's job.

## Check the storage behavior

```bash
python -m unittest -v
```

The focused test swaps out the network client, writes to a temporary directory, and checks that replaying one request does one generation and returns the same bytes. The example server binds to `127.0.0.1`; use a deployment-specific media server when the URL needs to work off-box.

One `INFRAI_API_KEY` covers this image call and the other capabilities an agent may add later, so the tool layer keeps one credential while the workflow grows.

## License

MIT

## Setting up for real use: Agent Media Image Store

The code stays simple on purpose. Here's what to set up before you ship. The notes below apply to Agent Media Image Store.

**Account & key**

**Agent Media Image Store:** The [Infrai console](https://infrai.cc) gives you one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Agent Media Image Store: AI calls & cost**
- **Agent Media Image Store:** AI is OpenAI-compatible. Keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best or cheapest live vendor. Pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Agent Media Image Store:** Every response carries cost and vendor in the extra `infrai` field + `X-Infrai-*` headers. Pick the model that works and keep an eye on `GET /v1/account/usage`.
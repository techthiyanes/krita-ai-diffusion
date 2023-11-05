"""Simple HTTP server for testing the installation process.
1) Run the docker.py script to download all required models.
2) Run this script to serve the model files on localhost.
3) Set environment variable HOSTMAP=1 to replace all huggingface / civitai urls.
"""

from aiohttp import web
from itertools import chain
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from ai_diffusion import resources

port = int(sys.argv[1]) if len(sys.argv) > 1 else 51222
dir = Path(__file__).parent / "docker"


def url_strip_host(url: str):
    return "/" + url.split("/", 3)[-1]


def get_path(m: resources.ModelResource):
    if m.kind is resources.ResourceKind.ip_adapter:
        return dir / "ip-adapter/" / m.filename
    else:
        return dir / m.folder / m.filename


models = chain(
    resources.required_models,
    resources.optional_models,
    resources.default_checkpoints,
    resources.upscale_models,
)
files = {url_strip_host(m.url): get_path(m) for m in models}

print("Serving files:")
for url, path in files.items():
    print(f"- {url} -> {path}")


async def handle(request: web.Request):
    file = files.get(request.path, None)
    if file and file.exists():
        print(f"Sending {file}")
        try:
            return web.FileResponse(file)
        except Exception as e:
            print(f"Failed to send {file}: {e}")
            return web.Response(status=500)
    elif file:
        print(f"File not found: {file}")
        return web.Response(status=404)
    else:
        print(f"File not found: {request.path}")
        return web.Response(status=404)


app = web.Application()
app.add_routes([web.get(url, handle) for url in files.keys()])
web.run_app(app, host="localhost", port=port)
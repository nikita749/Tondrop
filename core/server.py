from pathlib import Path

from aiohttp.web_fileresponse import FileResponse
from fastapi import FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import requests

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.storage_api import TonStorageAPI

app = FastAPI()

app.mount(
    "/core/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "core/static"),
    name="static",
)
templates = Jinja2Templates(directory="static")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )

@app.get("/test")
async def test_help_func():
    storage_cli_startup = '/home/strk/Downloads/ton/build/storage/storage-daemon/storage-daemon-cli -I 127.0.0.1:5555 -k /media/strk/LaCie/storage-db/storage/tondrop-storage/cli-keys/client -p /media/strk/LaCie/storage-db/storage/tondrop-storage/cli-keys/server.pub'

    api = TonStorageAPI(storage_cli_startup)

    if api.start_cli_session():
        result = str(api.get_provider_info())
        api.stop()
        return {"api result": result}




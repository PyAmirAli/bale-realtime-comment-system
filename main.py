from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.post_api import router as post_router
from api.auth_api import router as user_router
from websocket.comment_ws import router as ws_router
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request



app = FastAPI(
    title="Bale Comment Service",
    version="1.0.0"
)
templates = Jinja2Templates(directory="templates")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")












app.include_router(ws_router)

app.include_router(
    post_router,
    prefix="/api"
)

app.include_router(
    user_router,
    prefix="/api"
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


import uvicorn

uvicorn.run(app,host='0.0.0.0')


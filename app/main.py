from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routes_auth import router as auth_router
from app.routes_admin import router as admin_router
from app.routes_upload import router as upload_router
from app.routes_profile import router as profile_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(upload_router)
app.include_router(profile_router) 

app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request})

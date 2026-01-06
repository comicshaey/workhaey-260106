from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.routers.pages import router as pages_router
from app.routers.social_insurance import router as social_insurance_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)

    # templates
    env = Environment(
        loader=FileSystemLoader("app/templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    app.state.templates = __import__("starlette.templating").templating.Jinja2Templates(
        directory="app/templates"
    )

    # static
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # routers
    app.include_router(pages_router)
    app.include_router(social_insurance_router)

    return app

app = create_app()

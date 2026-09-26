from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import StockInsuffisant
from neosys_pharma.presentation.api.container import (
    ApplicationContainer,
    create_container,
)
from neosys_pharma.presentation.api.routes import router


def create_app(container: ApplicationContainer | None = None) -> FastAPI:
    application = FastAPI(
        title="NeoSys Pharma API",
        version="1.7.0",
        description="API du prototype pour la Grande Pharmacie des Forestiers",
    )
    application.state.container = container or create_container()
    web_directory = Path(__file__).with_name("web")
    application.mount("/assets", StaticFiles(directory=web_directory), name="assets")

    @application.middleware("http")
    async def desactiver_cache_interface(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        if request.url.path == "/gestion" or request.url.path.startswith("/assets/gestion"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response

    @application.get("/", include_in_schema=False)
    def accueil() -> RedirectResponse:
        return RedirectResponse(url="/encaissement")

    @application.get("/console", include_in_schema=False)
    def console_vente() -> FileResponse:
        return FileResponse(web_directory / "index.html")

    @application.get("/gestion", include_in_schema=False)
    def gestion() -> FileResponse:
        return FileResponse(
            web_directory / "gestion.html",
            headers={"Cache-Control": "no-store, max-age=0"},
        )

    @application.get("/vente", include_in_schema=False)
    def vente_web() -> FileResponse:
        return FileResponse(web_directory / "vente.html", headers={"Cache-Control": "no-store"})

    @application.get("/encaissement", include_in_schema=False)
    def encaissement_web() -> FileResponse:
        return FileResponse(
            web_directory / "encaissement.html", headers={"Cache-Control": "no-store"}
        )

    @application.exception_handler(StockInsuffisant)
    async def stock_insuffisant_handler(
        _request: Request, exception: StockInsuffisant
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exception)},
        )

    @application.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exception: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exception)},
        )

    application.include_router(router)
    return application


app = create_app()

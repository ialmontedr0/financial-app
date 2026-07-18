import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


class AppError(Exception):
    """Error base de la aplicacion."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(code="NOT_FOUND", message=f"{resource} no encontrado", status_code=404)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Autenticacion requerida"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Permisos insuficientes"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)


class ValidationError(AppError):
    def __init__(self, message: str = "Error de validacion", details: list[str] | None = None):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422)
        self.details = details or []


def register_error_handlers(app: FastAPI) -> None:
    """Manejador global de registro de error."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("App error", code=exc.code, message=exc.message, path=request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": getattr(exc, "details", []),
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no manejado", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Ha ocurrido un error inesperado.",
                },
            },
        )

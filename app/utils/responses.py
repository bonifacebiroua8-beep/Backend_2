# app/utils/responses.py — UbuntuTech v3.0
from fastapi.responses import JSONResponse
from typing import Any, Optional


def ok(data: Any, message: str = "OK", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data}
    )


def err(message: str, status_code: int = 400, details: Optional[Any] = None) -> JSONResponse:
    content = {"success": False, "message": message}
    if details:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content)

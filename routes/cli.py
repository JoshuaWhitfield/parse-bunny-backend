from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

router = APIRouter()

SUPPORTED_PLATFORMS = ["linux", "windows", "macos"]

@router.get("/download/cli")
async def download_cli(request: Request):
    user_agent = request.headers.get("user-agent", "").lower()

    # OS detection
    if "windows" in user_agent:
        modular = "windows"
        filename = "parse-bunny.exe"
        media_type = "application/vnd.microsoft.portable-executable"
    elif "macintosh" in user_agent or "mac os" in user_agent:
        modular = "macos"
        filename = "parse-bunny"
        media_type = "application/octet-stream"
    elif "linux" in user_agent:
        modular = "linux"
        filename = "parse-bunny"
        media_type = "application/octet-stream"
    else:
        return JSONResponse(
            {"error": "Unsupported OS. Supported: windows, linux, macos"},
            status_code=400
        )

    binary_path = Path(f"/var/www/parsebunnycli/assets/{modular}/{filename}")

    if not binary_path.exists():
        return JSONResponse(
            {"error": f"Binary not found for {modular}"},
            status_code=404
        )

    return FileResponse(
        path=binary_path,
        filename=filename,
        media_type=media_type
    )

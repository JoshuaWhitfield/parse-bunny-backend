from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.routes.organization import router as organization_router
from backend.routes.user import router as user_router
from backend.routes.backups import router as backups_router
from backend.routes.balance import router as balance_router
from backend.routes.otp import router as otp_router
from backend.routes.audit import router as audit_router 
from backend.routes.whitelist import router as whitelist_router
from backend.routes.cli import router as cli_router 
from backend.routes.stripe import router as stripe_router

# ---------------------------
# Create FastAPI app
# ---------------------------
app = FastAPI()

# ---------------------------
# Setup CORS (your original config)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - allows any frontend, including localhost:3000, etc
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Setup SlowAPI (Rate Limiting + Whitelist Localhost)
# ---------------------------
WHITELIST_IPS = {"127.0.0.1", "localhost"}

def custom_key_func(request):
    ip = get_remote_address(request)
    if ip in WHITELIST_IPS:
        return "whitelisted"
    return ip

limiter = Limiter(key_func=custom_key_func)

# Attach limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: PlainTextResponse("Too Many Requests", status_code=429))

# ---------------------------
# Load API Routers with /api prefix
# ---------------------------
app.include_router(organization_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(backups_router, prefix="/api")
app.include_router(balance_router, prefix="/api")
app.include_router(otp_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(whitelist_router, prefix="/api")
app.include_router(cli_router, prefix="/api")
app.include_router(stripe_router, prefix="/api")
# ---------------------------
# Debug: print loaded routes
# ---------------------------
print("[debug] Initializing Parse-Bunny Server...")
for route in app.routes:
    print(f" - {route.path} → {route.name}")
print("[debug] ✅ All routers loaded successfully.")

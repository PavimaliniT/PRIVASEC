from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.core.middleware import SecurityGatewayMiddleware
from app.services.seed import seed_database

# Import routers
from app.routers.auth import router as auth_router
from app.routers.privacy import router as privacy_router
from app.routers.crypto import router as crypto_router
from app.routers.visual_crypto import router as visual_crypto_router
from app.routers.steganography import router as steganography_router
from app.routers.intelligence import router as intelligence_router
from app.routers.incidents import router as incidents_router
from app.routers.simulation import router as simulation_router
from app.routers.audit import router as audit_router
from app.routers.security import router as security_router
from app.routers.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed initial database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_database(session)

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_FULL_NAME,
    description="Full-stack cybersecurity platform combining privacy engineering, ML threat detection, adaptive authentication, and cryptographic tools.",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Security Gateway Middleware (WAF pattern detection, rate limiting, security headers)
app.add_middleware(SecurityGatewayMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount Routers under /api
api_prefix = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=api_prefix)
app.include_router(privacy_router, prefix=api_prefix)
app.include_router(crypto_router, prefix=api_prefix)
app.include_router(visual_crypto_router, prefix=api_prefix)
app.include_router(steganography_router, prefix=api_prefix)
app.include_router(intelligence_router, prefix=api_prefix)
app.include_router(incidents_router, prefix=api_prefix)
app.include_router(simulation_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)
app.include_router(security_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestrators and monitoring agents."""
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

import time
import re
import hashlib
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.config import settings

# Suspicious pattern indicators for application-layer monitoring (educational/SOC telemetry)
SQLI_PATTERNS = [
    re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.IGNORECASE),
    re.compile(r"\b(UNION\s+ALL\s+SELECT|UNION\s+SELECT|SELECT\s+.*\s+FROM)\b", re.IGNORECASE),
    re.compile(r"\b(WAITFOR\s+DELAY|SLEEP\(\d+\)|BENCHMARK\(\d+)\b", re.IGNORECASE),
    re.compile(r"\b(OR\s+['\"]?1['\"]?\s*=\s*['\"]?1|AND\s+['\"]?1['\"]?\s*=\s*['\"]?1)\b", re.IGNORECASE)
]

XSS_PATTERNS = [
    re.compile(r"<script.*?>.*?</script.*?>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:\s*", re.IGNORECASE),
    re.compile(r"onerror\s*=\s*", re.IGNORECASE),
    re.compile(r"onload\s*=\s*", re.IGNORECASE)
]

PATH_TRAVERSAL = [
    re.compile(r"(\.\./|\.\.\\)", re.IGNORECASE)
]


class RateLimiter:
    """Sliding-window rate limiter with in-memory store and token buckets."""
    def __init__(self):
        # key -> list of timestamps
        self.requests: Dict[str, List[float]] = {}
        self.blocked_until: Dict[str, float] = {}

    def is_rate_limited(self, key: str, max_requests: int = 120, window_seconds: int = 60) -> Tuple[bool, int]:
        now = time.time()
        
        # Check if temporarily locked
        if key in self.blocked_until:
            if now < self.blocked_until[key]:
                retry_after = int(self.blocked_until[key] - now) + 1
                return True, retry_after
            else:
                del self.blocked_until[key]

        history = self.requests.get(key, [])
        history = [t for t in history if now - t < window_seconds]
        
        if len(history) >= max_requests:
            # Block for 30 seconds
            self.blocked_until[key] = now + 30
            self.requests[key] = history
            return True, 30

        history.append(now)
        self.requests[key] = history
        return False, 0


rate_limiter = RateLimiter()


class SecurityGatewayMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Extract and Pseudonymize Client IP
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "127.0.0.1")
        ip_token = hashlib.sha256(f"{client_ip}-{settings.SECRET_KEY}".encode("utf-8")).hexdigest()[:16]
        request.state.client_ip = client_ip
        request.state.ip_token = ip_token

        # 2. Extract Device Signature
        user_agent = request.headers.get("user-agent", "unknown")
        device_hash = hashlib.sha256(f"{user_agent}-{ip_token}".encode("utf-8")).hexdigest()[:16]
        request.state.device_hash = device_hash

        # 3. Rate Limiting Check (Skip static assets or docs)
        path = request.url.path
        if path.startswith("/api/"):
            # Limit auth endpoints more strictly
            max_limit = 20 if "/auth/login" in path else 150
            is_limited, retry_after = rate_limiter.is_rate_limited(f"rl:{ip_token}:{path}", max_requests=max_limit)
            if is_limited:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Excessive request volume detected.",
                        "retry_after_seconds": retry_after,
                        "ip_token": ip_token
                    },
                    headers={"Retry-After": str(retry_after)}
                )

        # 4. Request Inspection for attack indicators (Simulation & Gateway detection)
        query_str = str(request.url.query)
        detected_threats = []

        for p in SQLI_PATTERNS:
            if p.search(query_str):
                detected_threats.append("SQL_INJECTION_INDICATOR")
                break

        for p in XSS_PATTERNS:
            if p.search(query_str):
                detected_threats.append("XSS_INDICATOR")
                break

        for p in PATH_TRAVERSAL:
            if p.search(query_str):
                detected_threats.append("PATH_TRAVERSAL_INDICATOR")
                break

        request.state.detected_threats = detected_threats

        # 5. Process Request
        response: Response = await call_next(request)

        # 6. Apply Hardened Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss: http://localhost:* http://127.0.0.1:*; "
            "frame-ancestors 'none';"
        )

        return response

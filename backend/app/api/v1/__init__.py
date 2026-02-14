"""
API Router - Main API endpoints
"""
from fastapi import APIRouter

api_router = APIRouter()

# Import all endpoints
try:
    from app.api.v1.endpoints import auth
    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
except ImportError as e:
    print(f"Warning: Could not import auth endpoints: {e}")

try:
    from app.api.v1.endpoints import users
    api_router.include_router(users.router, prefix="/users", tags=["Users"])
except ImportError as e:
    print(f"Warning: Could not import users endpoints: {e}")

try:
    from app.api.v1.endpoints import usage
    api_router.include_router(usage.router, prefix="/usage", tags=["Usage Data"])
except ImportError as e:
    print(f"Warning: Could not import usage endpoints: {e}")

try:
    from app.api.v1.endpoints import predictions
    api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
except ImportError as e:
    print(f"Warning: Could not import predictions endpoints: {e}")

try:
    from app.api.v1.endpoints import recommendations
    api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
except ImportError as e:
    print(f"Warning: Could not import recommendations endpoints: {e}")

try:
    from app.api.v1.endpoints import alerts
    api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
except ImportError as e:
    print(f"Warning: Could not import alerts endpoints: {e}")

try:
    from app.api.v1.endpoints import patterns
    api_router.include_router(patterns.router, prefix="/patterns", tags=["Patterns"])
except ImportError as e:
    print(f"Warning: Could not import patterns endpoints: {e}")

from app.api.v1.endpoints import notifications

api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"]
)

from app.api.v1.endpoints import exports

api_router.include_router(
    exports.router,
    prefix="/exports",
    tags=["exports"]
)

from app.api.v1.endpoints import system

api_router.include_router(
    system.router,
    prefix="/system",
    tags=["system"]
)

# Simple health check
@api_router.get("/health")
async def health_check():
    """API health check"""
    return {"status": "healthy", "api_version": "v1"}
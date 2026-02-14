"""
System and provider status endpoints
"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_active_user
from app.models.models import User
from app.integrations.factory import ProviderFactory

router = APIRouter()


@router.get("/provider-status")
async def get_provider_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get status of all data providers"""
    status = ProviderFactory.get_provider_status()
    
    return {
        "providers": status,
        "mode": "production" if "Real" in str(status) else "development",
        "message": "System is using real APIs" if "Real" in str(status) else "System is using simulated data"
    }


@router.post("/refresh-providers")
async def refresh_providers(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh provider connections (admin only)"""
    # In production, add role-based access control
    await ProviderFactory.refresh_providers()
    
    return {
        "status": "success",
        "message": "Providers refreshed",
        "providers": ProviderFactory.get_provider_status()
    }


@router.get("/system-info")
async def get_system_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get complete system information"""
    import platform
    import sys
    
    return {
        "system": {
            "platform": platform.system(),
            "python_version": sys.version,
            "architecture": platform.machine()
        },
        "providers": ProviderFactory.get_provider_status(),
        "features": {
            "lstm_predictions": True,
            "rl_recommendations": True,
            "pattern_detection": True,
            "real_time_monitoring": True,
            "iot_ready": True
        }
    }
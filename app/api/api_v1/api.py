from fastapi import APIRouter

from app.api.api_v1.endpoints import calls, sms, calendar, configuration, test

api_router = APIRouter()

# Include all API endpoint routers
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(sms.router, prefix="/sms", tags=["sms"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(configuration.router, prefix="/configuration", tags=["configuration"])
api_router.include_router(test.router, prefix="/test", tags=["test"])
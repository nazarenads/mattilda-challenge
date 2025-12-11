from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("")
async def health_check():
    """
    Health check endpoint.
    Returns the current status of the API.
    """
    return JSONResponse(
        content={"status": "healthy"},
        status_code=200,
    )


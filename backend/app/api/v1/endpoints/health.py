from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Seedance Studio API", "version": "1.0.0"}

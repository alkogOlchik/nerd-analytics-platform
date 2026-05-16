from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/health")
def analytics_health():
    return {"status": "ok"}

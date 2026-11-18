from fastapi import FastAPI
from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import publish_everywhere

app = FastAPI(title="Automated Multi-Platform Posting API", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/posting", response_model=PostingResponse)
async def posting(request: PostingRequest):
    results = await publish_everywhere(request.message)
    return PostingResponse(success=any(item.status == "success" for item in results), results=results)

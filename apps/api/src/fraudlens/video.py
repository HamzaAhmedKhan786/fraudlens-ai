from typing import Protocol

import httpx
from pydantic import BaseModel, Field


class VideoInferenceRequest(BaseModel):
    object_uri: str = Field(pattern=r"^gs://[a-z0-9._-]+/.+$", max_length=2048)
    sample_fps: float = Field(default=1.0, gt=0, le=10)


class VideoInferenceResult(BaseModel):
    status: str
    classification: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    uncertainty: float | None = Field(default=None, ge=0, le=1)
    model_version: str
    faces_detected: int = 0
    frames_sampled: int = 0
    visual_adapter: str | None = None
    temporal_adapter: str | None = None
    experimental: bool = True
    error: str | None = None
    audit_metadata: dict[str, object] = Field(default_factory=dict)


class VideoInferenceAdapter(Protocol):
    async def infer(self, request: VideoInferenceRequest) -> VideoInferenceResult: ...


class DisabledVideoInferenceAdapter:
    async def infer(self, request: VideoInferenceRequest) -> VideoInferenceResult:
        return VideoInferenceResult(
            status="NOT_CONFIGURED",
            classification="UNKNOWN",
            model_version="none",
            error="Video inference is disabled; no authenticity claim was produced",
            audit_metadata={"object_uri": request.object_uri, "sample_fps": request.sample_fps},
        )


class HttpVideoInferenceAdapter:
    def __init__(self, endpoint: str, model_version: str, bearer_token: str | None = None) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model_version = model_version
        self.bearer_token = bearer_token

    async def infer(self, request: VideoInferenceRequest) -> VideoInferenceResult:
        headers = {"Authorization": f"Bearer {self.bearer_token}"} if self.bearer_token else {}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.endpoint}/v1/infer", headers=headers, json=request.model_dump()
                )
            response.raise_for_status()
            result = VideoInferenceResult.model_validate(response.json())
            result.experimental = True
            return result
        except (httpx.HTTPError, ValueError) as exc:
            return VideoInferenceResult(
                status="FAILED",
                classification="UNKNOWN",
                model_version=self.model_version,
                error=str(exc)[:500],
                audit_metadata={"object_uri": request.object_uri},
            )

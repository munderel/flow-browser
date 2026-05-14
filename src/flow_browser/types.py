from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from flow_browser.client import FlowBrowser


class Model(str, Enum):
    VEO_3_1 = "veo-3.1"
    VEO_3_1_FAST = "veo-3.1-fast"
    VEO_2 = "veo-2"


class AspectRatio(str, Enum):
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"
    SQUARE_1_1 = "1:1"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Project(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    url: str | None = None


class Ingredient(BaseModel):
    id: str
    name: str | None = None
    thumbnail_url: str | None = None


class Scene(BaseModel):
    id: str
    index: int
    project_id: str
    prompt: str | None = None
    video_url: str | None = None


class Video(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    scene_id: str | None = None
    project_id: str | None = None
    url: str | None = Field(default=None, description="CDN URL for the rendered MP4, when known")
    prompt: str | None = None
    model_name: Model | None = None

    _client: FlowBrowser | None = None

    def bind(self, client: FlowBrowser) -> Video:
        self._client = client
        return self

    async def download(self, path: str | Path) -> Path:
        if self._client is None:
            raise RuntimeError("Video is not bound to a FlowBrowser; call .bind(client) first")
        return await self._client.download_video(self, path)

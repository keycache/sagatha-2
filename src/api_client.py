import json
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel

from src.constants import IMAGE_API_URL, MUSIC_API_URL, NARRATION_API_URL
from src.utils.helper import timeit


class Data(BaseModel):
    value: str
    seed: int


class AssetResponse(BaseModel):
    prompt: str
    metadata: Dict
    data: List[Data]


class AspectRatio(str, Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    SQUARE = "square"


class Style(str, Enum):
    CARTOON = "cartoon"
    ANIMATED = "animated"
    REALISTIC = "realistic"


headers = {"accept": "application/json", "Content-Type": "application/json"}


def generate_narration(narration_texts: List[Dict[str, Any]], model_name: str = "test") -> None:
    payload = {
        "model_name": model_name,
        "count": 1,
        "prompts": narration_texts,
    }
    print(f"Generating narration with payload:\n{json.dumps(payload, indent=2)}")
    response = requests.post(
        NARRATION_API_URL,
        json=payload,
        headers=headers,
    )
    response.raise_for_status()
    return [AssetResponse.model_validate(asset) for asset in response.json()]


def generate_music(music_prompts: List[Dict[str, Any]], model_name: str = "small") -> None:
    payload = {
        "model_name": model_name,
        "count": 1,
        "prompts": music_prompts,
    }
    print(f"Generating music with payload:\n{json.dumps(payload, indent=2)}")
    response = requests.post(
        MUSIC_API_URL,
        json=payload,
        headers=headers,
    )
    response.raise_for_status()
    return [AssetResponse.model_validate(asset) for asset in response.json()]


@timeit
def generate_images(
    images_prompts: List[Dict[str, Any]],
    reference_image: Optional[str] = None,
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT,
    cache: bool = True,
    model_name: str = "test",
) -> List[AssetResponse]:
    payload = {
        "model_name": model_name,
        "count": 1,
        "prompts": images_prompts,
        "aspect_ratio": aspect_ratio.value,
        "reference_image": reference_image,
    }
    # print(f"Generating images with payload:\n{json.dumps(payload, indent=2)}")
    response = requests.post(
        IMAGE_API_URL,
        json=payload,
        headers=headers,
    )
    response.raise_for_status()
    return [AssetResponse.model_validate(asset) for asset in response.json()]


if __name__ == "__main__":
    out = generate_narration(
        narration_texts=[{"text": "blah blah", "seed": 0}],
    )
    print(out)

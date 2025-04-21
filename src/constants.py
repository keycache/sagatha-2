from collections import namedtuple
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

AspectRatioDetails = namedtuple("AspectRatioDetails", ["ratio", "mode", "device", "height", "width", "duration"])

# load_dotenv("../.env")

MODEL_NAME = "gemini-2.0-flash-exp"
IMAGE_API_URL = "http://127.0.0.1:8003/image"
MUSIC_API_URL = "http://127.0.0.1:8002/music"
NARRATION_API_URL = "http://127.0.0.1:8001/narration"
IMAGE_GENERATION_MODEL_NAME = "test"
VIDEO_FPS = 30
BACKGROUND_MUSIC_VOLUME = 0.3
BASE_PATH = ".data/story"
MUSIC_BASE_PATH = ".data/music"


class AspectRatio:
    AR_9_16 = AspectRatioDetails("9:16", "portrait", "mobile/phone", height=1080, width=1920, duration=178)
    AR_16_9 = AspectRatioDetails("16:9", "landscape", "desktop", height=1920, width=1080, duration=1800)
    AR_1_1 = AspectRatioDetails("1:1", "square", "mobile/phone", height=1024, width=1024, duration=178)

    def get_modes(self):
        return [ar.mode for ar in self.__class__.__dict__.values() if isinstance(ar, AspectRatioDetails)]

    def get_ratios(self):
        return [ar.ratio for ar in self.__class__.__dict__.values() if isinstance(ar, AspectRatioDetails)]

    def get_details_by_mode(self, mode: str) -> Optional[AspectRatioDetails]:
        for ar in self.__class__.__dict__.values():
            if isinstance(ar, AspectRatioDetails) and ar.mode == mode:
                return ar
        raise None


class ResourceTarget(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"


class ResourceMode(str, Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    SQUARE = "square"


class StructureType(str, Enum):
    exposition = "1-exposition"
    rising_action = "2-rising-action"
    climax = "3-climax"
    falling_action = "4-falling-action"
    resolution = "5-resolution"


if __name__ == "__main__":
    from typing import Literal

    from pydantic import BaseModel

    AR_Mode = Literal[tuple(AspectRatio().get_modes())]

    class Test(BaseModel):
        mode: AR_Mode

    test = Test(mode="1")
    test = Test(mode="1")

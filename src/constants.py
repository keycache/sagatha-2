from dotenv import load_dotenv

load_dotenv(".env")

MODEL_NAME = "gemini-2.0-flash-exp"
IMAGE_API_URL = "http://127.0.0.1:8003/image"
MUSIC_API_URL = "http://127.0.0.1:8002/music"
NARRATION_API_URL = "http://127.0.0.1:8001/narration"
IMAGE_GENERATION_MODEL_NAME = "test"
VIDEO_FPS = 30
BACKGROUND_MUSIC_VOLUME = 0.3

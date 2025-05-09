import base64
import hashlib
import json
import re
import time

# import nltk
from nltk.tokenize import word_tokenize

from src.constants import StructureType
from src.utils.file import save_file


def get_md5(text) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def to_kebab_case(input_string: str, limit=50) -> str:
    input_string = str(input_string)
    cleaned_string = re.sub(r"[^a-zA-Z0-9\s_]", "", input_string)
    kebab_string = re.sub(r"[_\s]+", "-", cleaned_string)
    return kebab_string.lower()[:limit]


def save_base64_image(base64_string, output_path) -> str:
    image_data = base64.b64decode(base64_string)
    return save_file(output_path, image_data, mode="wb")


def save_base64_audio(base64_string, output_path) -> str:
    audio_data = base64.b64decode(base64_string)
    return save_file(output_path, audio_data, mode="wb")


def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record start time
        result = func(*args, **kwargs)  # Call the original function
        end_time = time.time()  # Record end time
        execution_time = end_time - start_time  # Calculate execution time
        print(f"Method '{func.__name__}' executed in {execution_time:.4f} seconds.")
        return result

    return wrapper


def get_structure_prompts(structure_type: StructureType, prompts_file_path=".data/music/prompts.json"):
    with open(prompts_file_path, "r", encoding="ISO-8859-1") as file:
        data = file.read()
    data = json.loads(data)
    return data.get(structure_type.name, [])


def get_word_count(text: str) -> int:
    return len(word_tokenize(text))


if __name__ == "__main__":
    print(get_structure_prompts(StructureType.falling_action))

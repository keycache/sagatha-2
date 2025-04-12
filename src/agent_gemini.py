import os
import pathlib
import subprocess
from io import BytesIO
from typing import Optional

# from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from PIL.ImageFile import ImageFile
from pydantic import BaseModel

from src.constants import GEMINI_API_KEY

# res = load_dotenv("/Users/akashpatki/Documents/kash/code/moon/sagatha-2/.env")
# print(f"res------------: {res}")


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()


def get_config():
    return types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_modalities=["image", "text"],
        response_mime_type="text/plain",
    )


def generate_image(
    prompt, cover_image_path: str, model: str = "gemini-2.0-flash-exp-image-generation"
) -> Optional[ImageFile]:
    print("(generate_image)Generating image...")
    print(f"(generate_image)Prompt: {prompt}, Cover Image Path: {cover_image_path}")
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = get_config()
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(data=pathlib.Path(cover_image_path).read_bytes(), mime_type="image/png"),
            ],
        ),
    ]
    response = client.models.generate_content(model=model, contents=contents, config=config)

    try:
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                new_image = Image.open(BytesIO(part.inline_data.data))
                # new_image.save(target_file_path)
                # print(f"Image saved to {target_file_path}")
                # return target_file_path
                return new_image
    except Exception as e:
        print(f"(generate_image)Error: {e}\n{response.candidates[0]}")
        raise e


def generate_cover_image(
    prompt: str,
    ref_cover_image_path: str = None,
    model: str = "gemini-2.0-flash-exp-image-generation",
) -> Optional[ImageFile]:
    print("(generate_cover_image)Generating cover image...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = get_config()
    contents = []
    if ref_cover_image_path:
        contents.append(
            types.Part.from_bytes(data=pathlib.Path(ref_cover_image_path).read_bytes(), mime_type="image/png")
        )
    contents.append(types.Part.from_text(text=prompt))
    response = client.models.generate_content(model=model, contents=contents, config=config)

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            new_image = Image.open(BytesIO(part.inline_data.data))
            print("(generate_cover_image)Cover image generated successfully.")
            return new_image


def remove_watermark(image_path: str, output_path: str):
    WM_REMOVAL_EXECUTABLE_PYTHON_PATH = "/opt/homebrew/Caskroom/miniconda/base/envs/py312aiwatermark/bin/python"
    WM_REMOVAL_SCRIPT_PATH = "/Users/akashpatki/Documents/kash/code/github/WatermarkRemover-AI/image_processor.py"
    command = [
        WM_REMOVAL_EXECUTABLE_PYTHON_PATH,
        WM_REMOVAL_SCRIPT_PATH,
        image_path,
        output_path,
    ]

    print(f"(remove_watermark)Removing watermark from image: {image_path}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        print(f"Error generating narration: {result.stderr}")
    else:
        print(f"WM removal completed successfully: {output_path}")
        return output_path
    return None


def generate_raw_story(
    model: BaseModel,
    system_prompt: str,
    premise: str,
    chapter_count: int,
    model_id: str = "gemini-2.5-pro-preview-03-25",
) -> BaseModel:
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = {"response_mime_type": "application/json", "response_schema": model}
    user_prompt = f"Generate a story with {chapter_count} chapters. This is the story's premise: {premise}."

    contents = [
        types.Content(role="model", parts=[types.Part.from_text(text=system_prompt)]),
        types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]),
    ]
    print(f"(generate_raw_story)Generating story with model: {model_id}")
    print(f"(generate_raw_story)System Prompt: {system_prompt}")
    print(f"(generate_raw_story)User Prompt: {user_prompt}")
    response = client.models.generate_content(model=model_id, contents=contents, config=config)
    return response.parsed

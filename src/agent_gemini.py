import os
import pathlib
from io import BytesIO
from typing import Optional

# from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from PIL.ImageFile import ImageFile

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


def generate_cover_image(prompt: str, model: str = "gemini-2.0-flash-exp-image-generation") -> Optional[ImageFile]:
    print("(generate_cover_image)Generating cover image...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = get_config()
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    response = client.models.generate_content(model=model, contents=contents, config=config)

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            new_image = Image.open(BytesIO(part.inline_data.data))
            print("(generate_cover_image)Cover image generated successfully.")
            return new_image


if __name__ == "__main__":
    import json

    from src.models import Story

    story_path = ".data/story/varin-and-the-whispering-map.json"
    story_path = ".data/story/pistan-and-the-oceans-secret.json"

    with open(story_path, "r") as file:
        data = json.load(file)
    story = Story.model_validate(data)
    cover_image_path = story_path.replace(".json", "-cover-image.png")
    if not os.path.exists(cover_image_path):
        prompt = story.chapters[0].get_cover_image_prompt(protagonist=story.protagonist)
        print(f"Prompt: {prompt}")
        cover_image = generate_cover_image(prompt=prompt)
        cover_image.save(cover_image_path)
        print(f"Cover Image path: {cover_image_path}")
    else:
        print(f"Cover Image already exists: {cover_image_path}")

    image_prompts = story.chapters[0].get_image_prompts()
    # print(f"Image prompts: {image_prompts}")
    for i, image_prompt in enumerate(image_prompts):
        image_path = story_path.replace(".json", f"-image-{i}.png")
        if os.path.exists(image_path):
            print(f"Image already exists: {image_path}")
            continue
        image_prompt = story.chapters[0].get_image_prompt(prompt=image_prompt, protagonist=story.protagonist)
        print(f"({i})Image prompt: {image_prompt}")
        image = generate_image(cover_image=Image.open(cover_image_path), prompt=image_prompt)
        image.save(image_path)
        print(f"Image path: {image_path}")
        break

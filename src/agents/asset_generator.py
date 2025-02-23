import base64
from typing import List, Optional

from pydantic import BaseModel

from src.agents.agent_utils import (
    get_random_structured_story,
    save_asset_image_reference,
    save_assets_images,
    save_assets_music,
    save_assets_narration,
)
from src.agents.base import BaseAgent
from src.agents.response_models import SceneModel, StructuredStory
from src.api_client import AspectRatio, AssetResponse, Style, generate_images, generate_music, generate_narration
from src.constants import IMAGE_GENERATION_MODEL_NAME
from src.utils.helper import timeit


class ImageGeneratorParams(BaseModel):
    model_name: str = IMAGE_GENERATION_MODEL_NAME
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    style_name: Style = Style.CARTOON


class MusicGeneratorParams(BaseModel):
    model_name: str = "small"


class NarrationGeneratorParams(BaseModel):
    model_name: str = "afheart"  # ammichael
    format: str = "wav"


class AssetGenerator(BaseAgent):
    # @property
    # def agent(self):
    #     return Agent(
    #         model=Gemini(id=MODEL_NAME),
    #         system_prompt=ASSET_GENERATOR_SYSTEM_PROMPT,
    #         instructions=ASSET_GENERATOR_INSTRUCTIONS,
    #         response_model=AssetGeneratorResponseModel,
    #         structured_outputs=True,
    #     )

    def get_image_prompts(self, scenes: List[SceneModel]):
        return [
            {
                "text": scene.image_prompt,
            }
            for scene in scenes
        ]

    def get_music_prompts(self, scenes: List[SceneModel]):
        return [{"text": scene.music_prompt, "seed": 0} for scene in scenes]

    def get_narration_texts(self, scenes: List[SceneModel]):
        return [{"text": scene.narration_text, "seed": 0} for scene in scenes]

    def get_style_prompt(self, style_name: str):
        return f"2d cartoon, colorful picture"

    def get_reference_image(
        self, structured_story: StructuredStory, image_generation_params: ImageGeneratorParams
    ) -> Optional[str]:
        prompts = [
            {"text": f"{self.get_style_prompt(image_generation_params.style_name)} {structured_story.protogonist}"}
        ]
        print(f"Generating reference image for structured story: {structured_story.title}\nPrompts: {prompts}")
        images: List[AssetResponse] = generate_images(
            images_prompts=prompts,
            reference_image=None,
            aspect_ratio=image_generation_params.aspect_ratio,
            model_name=image_generation_params.model_name,
        )
        image_paths = save_asset_image_reference(
            structured_story,
            images,
            aspect_ratio=image_generation_params.aspect_ratio,
            model_name=image_generation_params.model_name,
        )
        if image_paths:
            with open(image_paths[0], "rb") as image_file:
                image_binary = image_file.read()
                return base64.b64encode(image_binary).decode("utf-8")
        return None

    def run(
        self,
        structured_story: StructuredStory,
        image_generation_params: ImageGeneratorParams,
        music_generation_params: MusicGeneratorParams,
        narration_generation_params: NarrationGeneratorParams,
        cache: bool = True,
    ) -> None:
        reference_image = self.get_reference_image(structured_story, image_generation_params)
        for i, scene_breakdown in enumerate(structured_story.scenes, start=1):
            ###Process the image prompts
            image_prompts = self.get_image_prompts(scene_breakdown)
            print(f"Generating ****images**** for chapter {i} with prompts: {image_prompts}")
            images: List[AssetResponse] = generate_images(
                image_prompts,
                reference_image=reference_image,
                aspect_ratio=image_generation_params.aspect_ratio,
                model_name=image_generation_params.model_name,
            )
            image_paths = save_assets_images(
                structured_story,
                images,
                chapter=i,
                aspect_ratio=image_generation_params.aspect_ratio,
                model_name=image_generation_params.model_name,
            )
            print(f"Saved ****images**** for chapter {i} to: {image_paths}")

            ###Process the music prompts
            music_prompts = self.get_music_prompts(scene_breakdown)
            print(f"Generating ****music**** for chapter {i} with prompts: {music_prompts}")
            music_assets: List[AssetResponse] = generate_music(
                music_prompts=music_prompts,
                model_name=music_generation_params.model_name,
            )
            music_paths = save_assets_music(
                structured_story=structured_story,
                music_assets=music_assets,
                chapter=i,
                model_name=music_generation_params.model_name,
            )
            print(f"Saved ****music**** for chapter {i} to: {music_paths}")

            ###Process the narration texts
            narration_texts = self.get_narration_texts(scene_breakdown)
            print(f"Generating ****narration**** for chapter {i} with texts: {narration_texts}")
            narration_assets = generate_narration(narration_texts, model_name=narration_generation_params.model_name)
            narration_audio_pathss = save_assets_narration(
                structured_story=structured_story,
                narration_assets=narration_assets,
                chapter=i,
                model_name=narration_generation_params.model_name,
                format=narration_generation_params.format,
            )
            print(f"Saved ****narration**** for chapter {i} to: {narration_audio_pathss}")


if __name__ == "__main__":
    path = r".data\stories\timmy-and-buster-a-tail-of-friendship\2-structured-story-timmy-and-buster-a-tail-of-friendship.json"
    structured_story = get_random_structured_story(path)
    # print(structured_story)
    AssetGenerator().run(
        structured_story,
        image_generation_params=ImageGeneratorParams(),
        music_generation_params=MusicGeneratorParams(),
        narration_generation_params=NarrationGeneratorParams(),
    )

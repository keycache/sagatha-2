import base64
from typing import List, Optional

from pydantic import BaseModel

from src.agents.agent_utils import (
    get_asset_image_reference_path,
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
from src.utils.file import read_file_as_base64
from src.utils.helper import timeit


class AssetGeneratorParams(BaseModel):
    enabled: bool = True


class ImageGeneratorParams(AssetGeneratorParams):
    model_name: str = IMAGE_GENERATION_MODEL_NAME
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    style_name: Style = Style.CARTOON


class MusicGeneratorParams(AssetGeneratorParams):
    model_name: str = "small"


class NarrationGeneratorParams(AssetGeneratorParams):
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

    def get_style_prompt(self, style_name: str):
        style = f"2D Cartoon Looney Tunes style/equivalent, whimsical and expressive characters, exaggerated features and emotions, versatile and adaptable for various storytelling purposes"
        style = "Tintin style Exaggerated, rubber-hose animation style with flexible, curvy lines and highly expressive features typical of classic 2D cartoons"
        style = "Clear, clean line art with precise details, muted colors and soft shading, evoking the classic comic style of Tintin."
        style = "2D Tintin style, line art with precise details, muted colors and soft shading."
        style = "cartoon digital painting art style, isolated on solid white background, adorable, big eyes, cute cartoon character"
        return style

    def get_image_prompts(self, scenes: List[SceneModel], style_name: str):
        return [
            {
                "text": f"{self.get_style_prompt(style_name)}. {scene.image_prompt}",
            }
            for scene in scenes
        ]

    def get_music_prompts(self, scenes: List[SceneModel]):
        return [{"text": scene.music_prompt, "seed": 0} for scene in scenes]

    def get_narration_texts(self, scenes: List[SceneModel]):
        return [{"text": scene.narration_text, "seed": 0} for scene in scenes]

    def get_reference_image(
        self, structured_story: StructuredStory, image_generation_params: ImageGeneratorParams
    ) -> Optional[str]:
        image_reference_path = get_asset_image_reference_path(
            structured_story, aspect_ratio=image_generation_params.aspect_ratio
        )
        if image_reference_path is not None:
            print(f"Found reference image at: {image_reference_path}")
            return read_file_as_base64(image_reference_path)

        prompts = [
            {
                "text": f"{self.get_style_prompt(image_generation_params.style_name)}. White backgound, face based on the following description: {structured_story.protagonist.description}"
            }
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
        if image_generation_params.enabled:
            reference_image = self.get_reference_image(structured_story, image_generation_params)
        for i, scene_breakdown in enumerate(structured_story.chapters, start=1):
            ###Process the image prompts
            if image_generation_params.enabled:
                image_prompts = self.get_image_prompts(scene_breakdown, style_name=image_generation_params.style_name)
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
            if music_generation_params.enabled:
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
            if narration_generation_params.enabled:
                narration_texts = self.get_narration_texts(scene_breakdown)
                print(f"Generating ****narration**** for chapter {i} with texts: {narration_texts}")
                narration_assets = generate_narration(
                    narration_texts, model_name=narration_generation_params.model_name
                )
                narration_audio_pathss = save_assets_narration(
                    structured_story=structured_story,
                    narration_assets=narration_assets,
                    chapter=i,
                    model_name=narration_generation_params.model_name,
                    format=narration_generation_params.format,
                )
                print(f"Saved ****narration**** for chapter {i} to: {narration_audio_pathss}")


if __name__ == "__main__":
    path = r".data\stories\the-boy-and-his-loyal-dog\2-structured-story-the-boy-and-his-loyal-dog.json"
    structured_story = get_random_structured_story(path)
    # print(structured_story)
    AssetGenerator().run(
        structured_story,
        image_generation_params=ImageGeneratorParams(enabled=False),
        music_generation_params=MusicGeneratorParams(enabled=True),
        narration_generation_params=NarrationGeneratorParams(enabled=False),
    )

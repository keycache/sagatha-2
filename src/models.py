import json
import os
import random
import time
from enum import Enum
from typing import List, Literal, Optional, Tuple

from PIL import Image
from PIL.ImageFile import ImageFile
from pydantic import BaseModel, Field

from src.agent_gemini import (
    generate_cover_image,
    generate_image,
    generate_raw_story,
    get_agent_response,
    remove_watermark,
)
from src.agent_narration import generate_narration
from src.constants import (
    BASE_PATH,
    MUSIC_BASE_PATH,
    AspectRatio,
    AspectRatioDetails,
    ResourceMode,
    ResourceTarget,
    StructureType,
)
from src.prompts import (
    get_system_prompt_for_narration_text_segmentation,
    get_system_prompt_for_short_form,
    get_system_prompt_reduce_word_count,
)
from src.styles import COVER_IMAGE_DESCRIPTION, ImageStyle
from src.utils.helper import get_structure_prompts, get_word_count, to_kebab_case

STRUCTURE_EXPOSITION_BG_MUSIC_PROMPTS = get_structure_prompts(StructureType.exposition)
STRUCTURE_RISING_ACTION_BG_MUSIC_PROMPTS = get_structure_prompts(StructureType.rising_action)
STRUCTURE_CLIMAX_BG_MUSIC_PROMPTS = get_structure_prompts(StructureType.climax)
STRUCTURE_FALLING_ACTION_BG_MUSIC_PROMPTS = get_structure_prompts(StructureType.falling_action)
STRUCTURE_RESOLUTION_BG_MUSIC_PROMPTS = get_structure_prompts(StructureType.resolution)

BG_MUSIC_PROMPTS = {
    StructureType.exposition: STRUCTURE_EXPOSITION_BG_MUSIC_PROMPTS,
    StructureType.rising_action: STRUCTURE_RISING_ACTION_BG_MUSIC_PROMPTS,
    StructureType.climax: STRUCTURE_CLIMAX_BG_MUSIC_PROMPTS,
    StructureType.falling_action: STRUCTURE_FALLING_ACTION_BG_MUSIC_PROMPTS,
    StructureType.resolution: STRUCTURE_RESOLUTION_BG_MUSIC_PROMPTS,
}


def get_prompt_bank(structure_type: StructureType = None) -> List[str]:
    if not structure_type:
        return (
            BG_MUSIC_PROMPTS[StructureType.climax]
            + BG_MUSIC_PROMPTS[StructureType.falling_action]
            + BG_MUSIC_PROMPTS[StructureType.exposition]
            + BG_MUSIC_PROMPTS[StructureType.rising_action]
            + BG_MUSIC_PROMPTS[StructureType.resolution]
        )
    return BG_MUSIC_PROMPTS[structure_type]


class VideoSettings(BaseModel):
    frame_rate: int = Field(default=30, description="Frame rate of the video")


class AudioSettings(BaseModel):
    bg_music_factor: float = Field(default=0.3, description="Volume of the background music")


AR_Mode = Literal[tuple(AspectRatio().get_modes())]


class WordCountResponse(BaseModel):
    text: str = Field(..., description="The output based on the input text and system prompt")


class NarrationToImagePrompt(BaseModel):
    text: str = Field(
        ...,
        description="A verbatim part of text of the narration, small enough to visually capture an aspect of the scene, but not long where the image would fail to capture the text. Every 2 sentences should be a new image.",
    )
    prompt: str = Field(..., description="The prompt to be used for generating the image")


class NarrationToImagePromptResponse(BaseModel):
    input: str = Field(..., description="The input text processed")
    data: List[NarrationToImagePrompt] = Field(
        ..., description="The list of image prompts generated from the input text"
    )
    input: str = Field(..., description="The input text processed")
    data: List[NarrationToImagePrompt] = Field(
        ..., description="The list of image prompts generated from the input text"
    )


class ImageSettings(BaseModel):
    image_style: ImageStyle = Field(
        default=ImageStyle.STORY_BOOK_CLASSIC,
        description="Image style to be used for generating images. This will be used to generate the images.",
    )
    aspect_ratio: AR_Mode = Field(AspectRatio.AR_9_16.mode, description="Aspect ratio of the image")


class StorySettings(BaseModel):
    chapter_count: int = Field(2, description="Number of chapters in the story")


class Settings(BaseModel):
    video: VideoSettings = Field(default=VideoSettings(), description="Video settings")
    audio: AudioSettings = Field(default=AudioSettings(), description="Audio settings")
    image: ImageSettings = Field(default=ImageSettings(), description="Image settings")
    story: StorySettings = Field(default=StorySettings(), description="Story settings")

    def save(self, file_path: str = ".data/settings.json") -> str:
        with open(file_path, "w") as fh:
            fh.write(self.model_dump_json(indent=2))
        print(f"Settings saved to {file_path}")
        return file_path


class AssetType(str, Enum):
    IMAGE = "image"
    NARRATION = "narration"
    BG_MUSIC = "background-music"


class Target(BaseModel):
    value: str = Field(
        ..., description="Target where the asset is saved. This will be the path to the asset in the system."
    )
    active: bool = Field(
        ...,
        description="Whether the target is active or not. This will be used to determine if the asset should be used.",
    )


class Asset(BaseModel):
    type: AssetType = Field(..., description="Type of the asset")
    text: str = Field(..., description="Prompt/Text for the asset")
    targets: Optional[List[Target]] = None
    # aspect_ratio: Optional[ResourceMode] = Field(ResourceMode.PORTRAIT, description="Aspect ratio of the asset")


class Character(BaseModel):
    name: str = Field(..., description="Character name")
    age: int = Field(..., description="Character age")
    physical_description: str = Field(..., description="Physical description of the character")
    personality: str = Field(..., description="Personality of the character")
    other_details: str = Field(..., description="Other details of the character")


class Prompt(BaseModel):
    image: List[str] = Field(..., description="List of image prompts that describe the scene")
    text: str = Field(..., description="The scene to be described")


class Scene(BaseModel):
    image: Optional[List[Asset]] = None
    #     Field(
    #         ...,
    #         description=f"""Image Assets to visually portray the scene. Depending on the length of narration, adjust the entries accordingly. Split the scene into images at logical breaks. Aim for segments that are visually distinct or can be represented in a manageable unit for image generation. Avoid creating a prompt that has too many details. Avoid making prompt excessively long. Ensure that the image assets are in order and relevant to the narration. The image assets should be in the same order as the narration. Ensure the image prompt always incudes at least the protagonist or maximum of 3 characters(including the protagonist) in the image prompt. A general thumb rule, one image for every 15-20 words or per logical group of actions in the narration text. The image prompts should be descriptive and focused on visual elements, suitable for a modern text-to-image diffusion model. Include the character descriptions, thier physical looks, in terms of thie heigh, dress, color, etc(relevant to story telling and keeping the character's look consistent).  Generate the prompt using the following template:
    # {IMAGE_PROMPT_FORMAT}
    # """,
    #     )
    narration: Asset = Field(
        ...,
        description="The text needed for narration of the scene. This is the text that will be read out loud. This progresses the story.",
    )

    def get_word_count(self):
        return len(self.narration.text.split(" "))


class Structure(BaseModel):
    type: StructureType = Field(..., description="Name of the structure")
    scenes: List[Scene] = Field(..., description="List of scenes in the structure")
    background_music: Asset = Field(
        ...,
        description=f"Background music asset that compliments the structure based on the scenes. Depending on the structure type, choose the prompt verbatim from {BG_MUSIC_PROMPTS}",
    )

    def get_word_count(self):
        total = 0
        for scene in self.scenes:
            total += scene.get_word_count()
        return total


class ResourceTargets(BaseModel):
    target_type: ResourceTarget = Field(
        ..., description="The target type of the resource. This will be the type of the resource in the target system."
    )
    url: str = Field(
        ..., description="The URL of the resource. This will be the URL to the resource in the target system."
    )


class Resource(BaseModel):
    mode: ResourceMode = Field(..., description="The mode/orientation of the resource.")
    value: str = Field(..., description="Value of the resource. Path to the resource in the (non-target)system.")
    targets: Optional[List[ResourceTargets]] = None


class Chapter(BaseModel):
    title: str = Field(..., description="Chapter title")
    description: str = Field(
        ...,
        description="Chapter description. 200 words max. Use empojis to make it more fun! Do not give away the plot.",
    )
    characters: List[Character] = Field(
        ..., description="List of characters in the chapter that are not the protagonist"
    )
    chapter_number: int = Field(..., description="Chapter number")
    structures: List[Structure] = Field(
        ...,
        description="Structures in the chapter. The end of the chapter should be a hook and includes the moral of the story.",
    )
    cover_image: Asset = Field(..., description=COVER_IMAGE_DESCRIPTION)
    resources: Optional[List[Resource]] = None
    # story: Optional["Story"] = Field(default=None, exclude=True)

    def add_resource(self, aspect_ratio: AspectRatioDetails, file_path: str) -> Resource:
        if self.resources is None:
            self.resources = []
        resources = list(filter(lambda x: x.value == file_path, self.resources))
        if resources:
            print(f"Resource already exists: {resources[0]}")
            return resources[0]
        resource = Resource(
            mode=aspect_ratio.mode,
            value=file_path,
        )
        self.resources.append(resource)
        print(f"Resource added: {resource}")
        return resource

    def get_structure(self, structure_name: str) -> Optional[Structure]:
        for structure in self.structures:
            if structure.type.value == structure_name:
                return structure
        return None

    def get_characters(self) -> List[str]:
        return [character.model_dump_json() for character in self.characters]

    def get_word_count(self):
        total = 0
        for structure in self.structures:
            total += structure.get_word_count()
        return total

    def get_image_prompts(self):
        image_prompts = []
        for structure in self.structures:
            for scene in structure.scenes:
                for asset in scene.image:
                    image_prompts.append(asset.text)
        return image_prompts

    def get_cover_image(self):
        return self.cover_image.text

    def get_image_prompt(
        self,
        prompt: str,
        aspect_ratio: AspectRatioDetails,
        protagonist: Character,
        style: ImageStyle = None,
    ) -> str:
        return f"""

Use the attached cover image as a reference for generating a {aspect_ratio.ratio} ratio ({aspect_ratio.mode})image based on the following prompt:
An {aspect_ratio.mode} image in the following style: {style.value}.

{prompt}

These are the details of the protagonist:
{protagonist.model_dump_json()}

These are the relevant characters in the chapter:
{[character.model_dump_json() for character in self.characters]}
Use only the relevant character descriptions from above to generate the image.

Specifically, the image must be in a {aspect_ratio.ratio} ({aspect_ratio.mode}) aspect ratio for {aspect_ratio.device} screens.
Generate image using the style from the attached image.
Do not generate image as a collage.
"""

    def get_cover_image_prompt(
        self,
        ref_cover_image_available: bool,
        aspect_ratio: AspectRatioDetails,
        style: ImageStyle,
        protagonist: Character,
    ) -> str:
        style_instructions = (
            "Generate image using the style from the attached image. Maintain the similar image style."
            if ref_cover_image_available
            else ""
        )
        prompt = f"""
Generate a {aspect_ratio.ratio} aspect ratio, {aspect_ratio.mode} image for the cover image of the chapter based on the following prompt:
A {aspect_ratio.mode} image, e.g. dimensions({aspect_ratio.width}x{aspect_ratio.height}) with following details:\n{self.cover_image.text}
Generate the image in the style of a {style.value}.

These are the details of the protagonist:
{protagonist.model_dump_json()}

These are the relevant characters in the chapter:
{[character.model_dump_json() for character in self.characters]}

Generate the image as a collage of all the characters in the chapter. Ensure the protagonist is present and title is displayed on the image. The only words allowed in the image are the chapter title. Do not include any other text in the image.

{style_instructions}
"""
        return prompt

    def generate_cover_image(
        self,
        aspect_ratio: AspectRatioDetails,
        style: ImageStyle,
        protagonist: Character,
        ref_cover_image_path: str = None,
    ) -> ImageFile:
        cover_image_prompt = self.get_cover_image_prompt(
            ref_cover_image_path=bool(ref_cover_image_path),
            aspect_ratio=aspect_ratio,
            style=style,
            protagonist=protagonist,
        )
        cover_image = generate_cover_image(prompt=cover_image_prompt)
        return cover_image


class Story(BaseModel):
    title: str = Field(..., description="Title of the story")
    moral: str = Field(..., description="The moral of the story")
    premise: Optional[str] = Field(None, description="The premise of the story, input by the user")
    protagonist: Character = Field(..., description="Main character of the story")
    chapters: List[Chapter] = Field(..., description="List of chapters in the story")

    # def model_post_init(self, *args, **kwargs):
    #     print("*" * 30)
    #     print(f"Post init for story: {self.title}")
    #     for chapter in self.chapters:
    #         chapter.story = self

    def post_process_structures_conform_word_count(self, aspect_ratio_details: AspectRatioDetails):
        print("Post processing structures to conform to word count...")
        schema = WordCountResponse.model_json_schema()
        for chapter in self.chapters:
            updated = False
            chapter_word_count = chapter.get_word_count()
            if not chapter_word_count > 1.1 * aspect_ratio_details.max_words_count:
                continue
            for structure in chapter.structures:
                for scene in structure.scenes:
                    narration_word_count = get_word_count(scene.narration.text)
                    system_prompt = get_system_prompt_reduce_word_count(
                        aspect_ratio_details.max_words_count, narration_word_count, schema=schema
                    )
                    response: WordCountResponse = get_agent_response(
                        system_prompt=system_prompt,
                        query=scene.narration.text,
                        model_id="gemini-2.0-flash",
                        response_model=WordCountResponse,
                    )
                    scene.narration.text = response.text
                    updated = True
                    print("Sleeping for 2 seconds to avoid rate limiting")
                    time.sleep(2)
            if updated:
                print(f"Chapter: {chapter.title} updated with new narration.")
                self.save()

    def post_process_structures_enrich_images(self):
        print("Post processing structures to enrich images...")
        schema = NarrationToImagePromptResponse.model_json_schema()
        system_prompt = get_system_prompt_for_narration_text_segmentation(schema=schema)
        for chapter in self.chapters:
            print(f"Processing chapter: {chapter.title}")
            for structure in chapter.structures:
                print(f"Processing structure: {structure.type.value}")
                for scene in structure.scenes:
                    response: NarrationToImagePromptResponse = get_agent_response(
                        response_model=NarrationToImagePromptResponse,
                        system_prompt=system_prompt,
                        query=scene.narration.text,
                        model_id="gemini-2.5-flash-preview-04-17",
                    )
                    scene.image = [Asset(type=AssetType.IMAGE, text=item.prompt) for item in response.data]
                    print("Sleeping for 2 seconds to avoid rate limiting")
                    self.save()
                    time.sleep(2)

    def post_process(self, aspect_ratio_details: AspectRatioDetails):
        self.post_process_structures_conform_word_count(aspect_ratio_details=aspect_ratio_details)
        self.post_process_structures_enrich_images()

    def get_base_image_prompt(self, chapter_number: int):
        return f"""
These are the details of the protagonist:
{self.protagonist.model_dump_json()}

These are the details of the secondary characters:
{self.chapters[chapter_number].get_characters()}

Generate a 9:16 ratio image for the cover image of the chapter based on the following prompt:
{self.chapters[chapter_number].get_cover_image()}
        """

    def get_word_count(self) -> int:
        for chapter in self.chapters:
            print(f"Chapter: {chapter.title} Word Count: {chapter.get_word_count()}")

    def save_cover_image(
        self, cover_image: ImageFile, chapter: Chapter, version: int, aspect_ratio: AspectRatioDetails
    ) -> str:
        story_folder = os.path.join(BASE_PATH, to_kebab_case(self.title))
        chapter_path = os.path.join(
            story_folder, f"{chapter.chapter_number}-{to_kebab_case(chapter.title)}", aspect_ratio.mode
        )
        os.makedirs(chapter_path, exist_ok=True)
        cover_image_path = os.path.join(chapter_path, f"{to_kebab_case(chapter.title)}-cover-image-{version}.jpg")
        cover_image.save(cover_image_path, optimize=True)
        return cover_image_path

    def save_image(self, image: ImageFile, chapter: Chapter, suffix: str, aspect_ratio: AspectRatioDetails) -> str:
        story_folder = os.path.join(BASE_PATH, to_kebab_case(self.title))
        chapter_path = os.path.join(
            story_folder, f"{chapter.chapter_number}-{to_kebab_case(chapter.title)}", aspect_ratio.mode
        )
        os.makedirs(chapter_path, exist_ok=True)
        image_path = os.path.join(chapter_path, f"{to_kebab_case(chapter.title)}-image-{suffix}.jpg")
        image.save(image_path, optimize=True)
        return image_path

    def get_active_target(self, asset: Asset) -> Optional[Target]:
        if asset.targets is None:
            return None
        for target in asset.targets:
            if target.active and os.path.exists(target.value):
                return target

    def get_reference_cover_image(self, chapter: Chapter, aspect_ratio: AspectRatioDetails) -> bool:
        ref_cover_image_path = None
        if chapter.chapter_number != 1:
            ref_cover_image_path = self.get_cover_image_path(self.chapters[0], aspect_ratio)
        return ref_cover_image_path

    def generate_cover_image(
        self, chapter: Chapter, aspect_ratio: AspectRatioDetails, style: ImageStyle, force=False
    ) -> str:
        cover_image_target = self.get_active_target(chapter.cover_image)
        if force or cover_image_target is None:
            print(f"(generate_cover_image)Generating Cover Image for {chapter.title}")
            ref_cover_image_path = self.get_reference_cover_image(chapter, aspect_ratio)

            cover_image_prompt = chapter.get_cover_image_prompt(
                aspect_ratio=aspect_ratio,
                style=style,
                ref_cover_image_available=bool(ref_cover_image_path),
                protagonist=self.protagonist,
            )
            cover_image: ImageFile = generate_cover_image(
                prompt=cover_image_prompt,
                ref_cover_image_path=ref_cover_image_path,
            )
            print(f"(generate_cover_image)Cover Image generated: {cover_image.width}x{cover_image.height}")
            target_version = 0 if chapter.cover_image.targets is None else len(chapter.cover_image.targets)
            cover_image_path = self.save_cover_image(
                cover_image, chapter, version=target_version, aspect_ratio=aspect_ratio
            )
            remove_watermark(cover_image_path, cover_image_path)
            cover_image = cover_image.resize((aspect_ratio.width, aspect_ratio.height))
            cover_image_path = self.save_cover_image(
                cover_image, chapter, version=target_version, aspect_ratio=aspect_ratio
            )

            _ = self.handle_asset(chapter.cover_image, cover_image_path)
        else:
            print(f"(generate_cover_image)Cover Image already exists: {cover_image_target.value}")
            cover_image_path = cover_image_target.value
            cover_image = Image.open(cover_image_target.value)
        print(f"(generate_cover_image)Cover Image processing complete: {cover_image_path}")
        return cover_image_path

    def _get_suffix(self, chapter: Chapter, asset: Asset) -> Optional[str]:
        for i, structure in enumerate(chapter.structures):
            for j, scene in enumerate(structure.scenes):
                if asset.type == AssetType.IMAGE:
                    for k, image_asset in enumerate(scene.image):
                        if image_asset == asset:
                            return f"{i}-{j}-{k}"
                elif asset.type == AssetType.NARRATION:
                    if scene.narration == asset:
                        return f"{i}-{j}"

    def generate_image(
        self,
        image_asset: Asset,
        chapter: Chapter,
        aspect_ratio: AspectRatioDetails,
        style: ImageStyle,
        image_prompt: str = None,
        force=False,
    ) -> str:
        suffix = self._get_suffix(chapter, image_asset)
        image_target = self.get_active_target(image_asset)
        if force or image_target is None:
            print(f"(generate_image)Generating Image for {chapter.title} - {image_asset.text}")
            cover_image_path = self.generate_cover_image(chapter=chapter, aspect_ratio=aspect_ratio, style=style)

            image_prompt = image_prompt or chapter.get_image_prompt(
                image_asset.text, aspect_ratio=aspect_ratio, style=style, protagonist=self.protagonist
            )
            image: ImageFile = generate_image(prompt=image_prompt, cover_image_path=cover_image_path)
            # image: ImageFile = generate_image(prompt=image_prompt, cover_image=Image.open(cover_image_path))

            # handle the targets in image_asset
            target_version = 0 if image_asset.targets is None else len(image_asset.targets)
            image_path = self.save_image(image, chapter, suffix=f"{suffix}-{target_version}", aspect_ratio=aspect_ratio)
            # post process - resize, remove watermark, etc.
            remove_watermark(image_path, image_path)
            image = image.resize((aspect_ratio.width, aspect_ratio.height))
            image_path = self.save_image(image, chapter, suffix=f"{suffix}-{target_version}", aspect_ratio=aspect_ratio)
            _ = self.handle_asset(image_asset, image_path)
        else:
            print(f"(generate_image)Image already exists: {image_target.value}")
            image_path = image_target.value
            image = Image.open(image_target.value)

        print(f"Image processing complete: {image_path}")
        return image_path

    def get_narration_path(self, narration: Asset, chapter: Chapter) -> str:
        suffix = self._get_suffix(chapter, narration)
        story_folder = os.path.join(BASE_PATH, to_kebab_case(self.title))
        chapter_path = os.path.join(story_folder, f"{chapter.chapter_number}-{to_kebab_case(chapter.title)}")
        os.makedirs(chapter_path, exist_ok=True)
        narration_path = os.path.join(chapter_path, f"{to_kebab_case(chapter.title)}-narration-{suffix}.wav")
        return narration_path

    def generate_narration(self, narration: Asset, chapter: Chapter, force=False):
        narration_target = self.get_active_target(narration)
        print(f"Active target: {narration_target}")
        if force or narration_target is None:
            narration_path = self.get_narration_path(narration, chapter)
            narration_path = generate_narration(narration.text, narration_path)
            print(f"Narration generation complete at: {narration_path} for: {narration.text}")
            if not narration_path:
                raise Exception("Narration generation failed.")
            self.handle_asset(narration, narration_path)
            print(f"Narration generated successfully: {narration_path}")
        else:
            print(f"Narration already exists: {narration_target.value}")

    def handle_asset(self, asset: Asset, target_value: str):
        targets = [Target(value=target.value, active=False) for target in (asset.targets or [])]
        target = Target(value=target_value, active=True)
        targets.append(target)
        asset.targets = targets
        print(f"Asset targets: {asset.targets}")
        self.save()
        return targets

    def generate_images(self, chapter_index: int, aspect_ratio: AspectRatioDetails, style: ImageStyle) -> List[str]:
        story_image_paths = []
        for i, chapter in enumerate(self.chapters):
            print(f"Chapter: {chapter.title} Word Count: {chapter.get_word_count()}")
            if chapter_index is not None and i != chapter_index:
                continue
            cover_image_path = self.generate_cover_image(chapter=chapter, aspect_ratio=aspect_ratio, style=style)
            story_image_paths.append(cover_image_path)
            for j, structure in enumerate(chapter.structures):
                for k, scene in enumerate(structure.scenes):
                    for l, asset in enumerate(scene.image):
                        print("--" * 20)
                        print(f"({l+1}/{len(scene.image)})Processing image for {structure.type.value}")
                        image_path = self.generate_image(asset, chapter, aspect_ratio=aspect_ratio, style=style)
                        story_image_paths.append(image_path)
                        print("Sleeping for 10 seconds to avoid rate limiting")
                        print("--" * 20)
                        time.sleep(10)
        print(f"Story Image Paths: {story_image_paths}")
        return story_image_paths

    def get_story_folder(self):
        story_folder = os.path.join(BASE_PATH, to_kebab_case(self.title))
        os.makedirs(story_folder, exist_ok=True)
        return story_folder

    def get_story_path(self):
        return os.path.join(self.get_story_folder(), f"{to_kebab_case(self.title)}.json")

    def save(self, file_path: str = None) -> str:
        if file_path is None:
            file_path = self.get_story_path()

        with open(file_path, "w") as fh:
            fh.write(self.model_dump_json(indent=2))
        print(f"Story saved to {file_path}")
        return file_path

    def reset_images(self):
        for chapter in self.chapters:
            for structure in chapter.structures:
                for scene in structure.scenes:
                    for asset in scene.image:
                        asset.targets = None

        self.save()

    def reset_cover_image(self):
        for chapter in self.chapters:
            chapter.cover_image.targets = None
        self.save()

    def reset_backgound_music(self):
        for chapter in self.chapters:
            for structure in chapter.structures:
                structure.background_music.targets = None
        self.save()

    def reset_narrations(self):
        for chapter in self.chapters:
            for structure in chapter.structures:
                for scene in structure.scenes:
                    scene.narration.targets = None
        self.save()

    def reset_assets(self, asset_type: AssetType = None):
        if asset_type in (AssetType.IMAGE, None):
            self.reset_images()
            self.reset_cover_image()
        if asset_type in (AssetType.NARRATION, None):
            self.reset_narrations()
        if asset_type in (AssetType.BG_MUSIC, None):
            self.reset_backgound_music()
        self.save()
        print("Assets reset successfully.")

    def are_targets_available(self, asset: Asset) -> bool:
        if asset.targets is None:
            return False
        if not any([os.path.exists(target.value) for target in asset.targets]):
            return False
        return True

    def are_targets_valid(self, asset: Asset) -> bool:
        if not self.are_targets_available(asset):
            return False
        if self.get_active_target(asset) is None:
            return False
        return True

    def validate_narration(self, chapter_index: int = None):
        missing = []
        for i, chapter in enumerate(self.chapters):
            if chapter_index is not None and i != chapter_index:
                continue
            for j, structure in enumerate(chapter.structures):
                for k, scene in enumerate(structure.scenes):
                    if not self.are_targets_available(scene.narration):
                        missing.append(
                            {
                                "chapter": i,
                                "structure": j,
                                "scene": k,
                                "narration": scene.narration.text,
                            }
                        )

        return missing

    def validate_background_music(self, chapter_index: int = None):
        missing = []
        for i, chapter in enumerate(self.chapters):
            if chapter_index is not None and i != chapter_index:
                continue
            for j, structure in enumerate(chapter.structures):
                if not self.are_targets_available(structure.background_music):
                    missing.append(
                        {
                            "chapter": i,
                            "structure": j,
                            "background_music": structure.background_music.text,
                        }
                    )
        return missing

    def validate_cover_image(self, chapter_index: int = None):
        missing = []
        for i, chapter in enumerate(self.chapters):
            if chapter_index is not None and i != chapter_index:
                continue
            if not self.are_targets_available(chapter.cover_image):
                missing.append(
                    {
                        "chapter": i,
                        "cover_image": chapter.cover_image.text,
                    }
                )
        return missing

    def validate_images(self, chapter_index: int = None) -> dict:
        missing = []
        for i, chapter in enumerate(self.chapters):
            if chapter_index is not None and i != chapter_index:
                continue
            for j, structure in enumerate(chapter.structures):
                for k, scene in enumerate(structure.scenes):
                    for l, asset in enumerate(scene.image):
                        if not self.are_targets_available(asset):
                            missing.append(
                                {
                                    "chapter": i,
                                    "structure": j,
                                    "scene": k,
                                    "image_index": l,
                                    "image": asset.text,
                                }
                            )
        return missing

    def validate_assets(self, chapter_index: int = None) -> dict:
        return {
            "image": self.validate_images(chapter_index),
            "narration": self.validate_narration(chapter_index),
            "background_music": self.validate_background_music(chapter_index),
            "cover_image": self.validate_cover_image(chapter_index),
        }

    def generate_narrations(self, chapter_index: int = None) -> List[str]:
        narration_paths = []
        for i, chapter in enumerate(self.chapters):
            if chapter_index is not None and i != chapter_index:
                continue
            for structure in chapter.structures:
                for i, scene in enumerate(structure.scenes):
                    print(f"({i+1}/{len(structure.scenes)})Processing narration for {structure.type.value}")
                    narration_path = self.generate_narration(scene.narration, chapter)
                    narration_paths.append(narration_path)
        return narration_paths

    def generate_background_music(self, chapter_index: int = None):
        for i, chapter in enumerate(self.chapters):
            if chapter_index is not None and i != chapter_index:
                continue
            print(f"Chapter: {chapter.title} Word Count: {chapter.get_word_count()}")
            for structure in chapter.structures:
                structure_prompts = get_structure_prompts(structure.type)
                background_music = structure.background_music
                background_music_target = self.get_active_target(background_music)
                print(f"Active target: {background_music_target}")
                if background_music_target is None:
                    try:
                        if background_music.text not in structure_prompts:
                            print(
                                f"({structure.type})Background music prompt not found: Randomly assigning one instead of: {background_music.text}"
                            )
                            background_music.text = random.choice(structure_prompts)
                        print(f"Generating background music for: {background_music.text}")
                        music_path = os.path.join(
                            MUSIC_BASE_PATH,
                            structure.type.name,
                            f"{to_kebab_case(background_music.text)}.wav",
                        )
                        print(f"Music path: {music_path}")
                        self.handle_asset(background_music, music_path)
                    except Exception as e:
                        print(f"Error generating background music: {e}")
                        print(structure_prompts, structure.type, list(BG_MUSIC_PROMPTS.keys()))
                        raise e

    def get_asset_by_target_value(self, value: str) -> Optional[Tuple[Asset, Chapter]]:
        def _get_target_by_value(targets: List[Target], value: str) -> Optional[Target]:
            for target in targets:
                if target.value == value:
                    return target
            return None

        for chapter in self.chapters:
            for structure in chapter.structures:
                for scene in structure.scenes:
                    for asset in scene.image:
                        if _get_target_by_value(asset.targets, value) is not None:
                            return asset, chapter
                    if _get_target_by_value(scene.narration.targets, value) is not None:
                        return scene.narration, chapter
                if _get_target_by_value(structure.background_music.targets, value) == value:
                    return structure.background_music, chapter
        return None, None

    def get_cover_image_path(self, chapter: Chapter, aspect_ratio: AspectRatioDetails) -> Optional[str]:
        cover_image_target = self.get_active_target(chapter.cover_image)
        if cover_image_target:
            return cover_image_target.value

        # story_folder = os.path.join(BASE_PATH, to_kebab_case(self.title))
        # chapter_path = os.path.join(
        #     story_folder, f"{chapter.chapter_number}-{to_kebab_case(chapter.title)}", aspect_ratio.mode
        # )
        # file_paths = sorted(get_file_paths_with_text(chapter_path, suffix="-cover-image-"))
        # print(f"File paths: {file_paths}, chapter_path: {chapter_path}")
        # return file_paths[-1] if file_paths else None
        # return cover_image_path if os.path.exists(cover_image_path) else None

    @staticmethod
    def generate_short_story(premise, chapter_count=8, post_process: bool = False) -> str:

        system_prompt = get_system_prompt_for_short_form(story_schema=Story.model_json_schema())
        story: Story = generate_raw_story(
            model=Story, system_prompt=system_prompt, premise=premise, chapter_count=chapter_count
        )
        print(f"Generated story: {story.title}")
        if post_process:
            story.post_process()
        return story.save()

    def add_resource(self, chapter: Chapter, aspect_ratio: AspectRatioDetails, file_path: str):
        chapter.add_resource(aspect_ratio=aspect_ratio, file_path=file_path)
        self.save()

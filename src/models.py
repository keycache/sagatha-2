import json
import os
import random
import time
from enum import Enum
from typing import List, Optional

from PIL import Image
from PIL.ImageFile import ImageFile
from pydantic import BaseModel, Field

from src.agent_gemini import (
    generate_cover_image,
    generate_image,
    generate_raw_story,
    remove_watermark,
)
from src.agent_narration import generate_narration
from src.constants import BASE_PATH, MUSIC_BASE_PATH, AspectRatioDetails, StructureType
from src.prompts import SYSTEM_PROMPT_SHORTS
from src.utils.helper import get_structure_prompts, to_kebab_case

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
    image: List[Asset] = Field(
        ...,
        description="Image Assets to visually portray the scene. Depending on the length of narration, plas adjust the entries accordingly. Thumb rule: 1 image per 20-30 words of narration. Ensure that the image assets are relevant to the narration and in order. The image assets should be in the same order as the narration.",
    )
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
    cover_image: Asset = Field(
        ...,
        description="Cover image asset that represents the chapter. The image should be a collage of all the characters in the chapter. The image should also include the chapter title.",
    )

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
        protagonist: Character,
        aspect_ratio: AspectRatioDetails,
    ) -> str:
        return f"""
These are the details of the protagonist:
{protagonist.model_dump_json()}

These are the details of the secondary characters:
{self.get_characters()}

Use the attached cover image as a reference for generating a {aspect_ratio.ratio} ratio ({aspect_ratio.mode})image based on the following prompt:
A detailed {aspect_ratio.mode} view of {prompt}. Specifically, the image must be in a {aspect_ratio.ratio} ({aspect_ratio.mode}) aspect ratio for {aspect_ratio.device} screens.
Generate image using the style from the attached image.
Do not generate image as a collage.
"""

    def get_cover_image_prompt(
        self, protagonist: Character, ref_cover_image_available: bool, aspect_ratio: AspectRatioDetails
    ) -> str:
        style_instructions = (
            "Generate image using the style from the attached image" if ref_cover_image_available else ""
        )
        prompt = f"""
These are the details of the protagonist:
{protagonist.model_dump_json()}

These are the details of the secondary characters:
{self.get_characters()}

Generate a {aspect_ratio} aspect ratio {aspect_ratio.mode} image for the cover image of the chapter based on the following prompt:
A detailed {aspect_ratio.mode} of {self.cover_image.text}

The only words allowed in the image are the chapter title. Do not include any other text in the image.
The tile and the characters should be in the center 70% of the image.
{style_instructions}
"""
        return prompt

    def generate_cover_image(
        self,
        protagonist: Character,
        aspect_ratio: AspectRatioDetails,
        ref_cover_image_path: str = None,
    ) -> ImageFile:
        cover_image_prompt = self.get_cover_image_prompt(
            protagonist=protagonist, ref_cover_image_path=bool(ref_cover_image_path), aspect_ratio=aspect_ratio
        )
        cover_image = generate_cover_image(prompt=cover_image_prompt)
        return cover_image

    # def generate_images(self, protagonist: Character):

    #     cover_image = self.generate_cover_image(protagonist=protagonist)
    #     for structure in self.structures:
    #         for scene in structure.scenes:
    #             for asset in scene.image:
    #                 image_prompt = self.get_image_prompt(asset.text, protagonist=protagonist)
    #                 image = generate_image(prompt=image_prompt, cover_image=cover_image)
    #                 asset.target[0].value = image


class Story(BaseModel):
    title: str = Field(..., description="Title of the story")
    moral: str = Field(..., description="The moral of the story")
    protagonist: Character = Field(..., description="Main character of the story")
    chapters: List[Chapter] = Field(..., description="List of chapters in the story")

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
        cover_image_path = os.path.join(chapter_path, f"{to_kebab_case(chapter.title)}-cover-image-{version}.png")
        cover_image.save(cover_image_path)
        return cover_image_path

    def save_image(self, image: ImageFile, chapter: Chapter, suffix: str, aspect_ratio: AspectRatioDetails) -> str:
        story_folder = os.path.join(BASE_PATH, to_kebab_case(self.title))
        chapter_path = os.path.join(
            story_folder, f"{chapter.chapter_number}-{to_kebab_case(chapter.title)}", aspect_ratio.mode
        )
        os.makedirs(chapter_path, exist_ok=True)
        image_path = os.path.join(chapter_path, f"{to_kebab_case(chapter.title)}-image-{suffix}.png")
        image.save(image_path)
        return image_path

    def get_active_target(self, asset: Asset) -> Optional[Target]:
        if asset.targets is None:
            return None
        for target in asset.targets:
            if target.active and os.path.exists(target.value):
                return target

    def generate_cover_image(self, chapter: Chapter, aspect_ratio: AspectRatioDetails, force=False) -> str:
        cover_image_target = self.get_active_target(chapter.cover_image)
        if force or cover_image_target is None:
            print(f"(generate_cover_image)Generating Cover Image for {chapter.title}")
            ref_cover_image_path = None
            if chapter.chapter_number != 1:
                ref_cover_image_path = self.get_cover_image_path(self.chapters[0], aspect_ratio)
                print(f"(generate_cover_image)Ref Cover Image path: {ref_cover_image_path}")

            cover_image_prompt = chapter.get_cover_image_prompt(
                protagonist=self.protagonist,
                aspect_ratio=aspect_ratio,
                ref_cover_image_available=bool(ref_cover_image_path),
            )
            cover_image: ImageFile = generate_cover_image(
                prompt=cover_image_prompt,
                ref_cover_image_path=ref_cover_image_path,
            )
            target_version = 0 if chapter.cover_image.targets is None else len(chapter.cover_image.targets)
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
        self, image_asset: Asset, chapter: Chapter, aspect_ratio: AspectRatioDetails, force=False
    ) -> str:

        suffix = self._get_suffix(chapter, image_asset)
        image_target = self.get_active_target(image_asset)
        if force or image_target is None:
            print(f"(generate_image)Generating Image for {chapter.title} - {image_asset.text}")
            cover_image_path = self.generate_cover_image(
                chapter=chapter,
                aspect_ratio=aspect_ratio,
            )

            image_prompt = chapter.get_image_prompt(
                image_asset.text,
                protagonist=self.protagonist,
                aspect_ratio=aspect_ratio,
            )
            image: ImageFile = generate_image(prompt=image_prompt, cover_image_path=cover_image_path)
            # image: ImageFile = generate_image(prompt=image_prompt, cover_image=Image.open(cover_image_path))

            # handle the targets in image_asset
            target_version = 0 if image_asset.targets is None else len(image_asset.targets)
            image_path = self.save_image(image, chapter, suffix=f"{suffix}-{target_version}", aspect_ratio=aspect_ratio)
            # post process - resize, remove watermark, etc.
            remove_watermark(image_path, image_path)
            image = image.resize((aspect_ratio.height, aspect_ratio.width))
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

    def generate_images(self, aspect_ratio: AspectRatioDetails) -> List[str]:
        story_image_paths = []
        for i, chapter in enumerate(self.chapters):
            print(f"Chapter: {chapter.title} Word Count: {chapter.get_word_count()}")
            cover_image_path = self.generate_cover_image(chapter=chapter, aspect_ratio=aspect_ratio)
            story_image_paths.append(cover_image_path)
            for j, structure in enumerate(chapter.structures):
                for k, scene in enumerate(structure.scenes):
                    for i, asset in enumerate(scene.image):
                        print("--" * 20)
                        print(f"({i+1}/{len(scene.image)})Processing image for {structure.type.value}")
                        image_path = self.generate_image(asset, chapter, aspect_ratio=aspect_ratio)
                        story_image_paths.append(image_path)
                        print("Sleeping for 10 seconds to avoid rate limiting")
                        time.sleep(10)
            break
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

    def validate_assets(self, chapter_number: int = None) -> dict:
        missing = {
            "image": [],
            "narration": [],
            "background_music": [],
        }
        for chapter in self.chapters:
            if chapter_number is not None and chapter.chapter_number != chapter_number:
                continue
            for structure in chapter.structures:
                for scene in structure.scenes:
                    for asset in scene.image:
                        if asset.targets is None:
                            missing["image"].append(asset.text)
                        else:
                            target = self.get_active_target(asset)
                            if not os.path.exists(target.value):
                                missing["image"].append(asset.text)
                    if scene.narration.targets is None:
                        missing["narration"].append(scene.narration.text)
                    else:
                        target = self.get_active_target(scene.narration)
                        if not os.path.exists(target.value):
                            missing["narration"].append(scene.narration.text)
                if structure.background_music.targets is None:
                    missing["background_music"].append(structure.background_music.text)
                else:
                    target = self.get_active_target(structure.background_music)
                    # print(f"Target: {target}, {structure.background_music.text}")
                    if target is None:
                        print(f"-------{structure.background_music}")
                    if not os.path.exists(target.value):
                        missing["background_music"].append(structure.background_music.text)
        return missing

    def generate_narrations(self, chapter_number: int = None) -> List[str]:
        narration_paths = []
        for chapter in self.chapters:
            if chapter_number is not None and chapter.chapter_number != chapter_number:
                continue
            for structure in chapter.structures:
                for i, scene in enumerate(structure.scenes):
                    print(f"({i+1}/{len(structure.scenes)})Processing narration for {structure.type.value}")
                    narration_path = self.generate_narration(scene.narration, chapter)
                    narration_paths.append(narration_path)
        return narration_paths

    def generate_background_music(self):
        for chapter in self.chapters:
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

    def validate_background_music(self):
        prompts = get_prompt_bank()
        count = 0
        for chapter in self.chapters:
            for structure in chapter.structures:
                if structure.background_music.text not in prompts:
                    print(f"({structure.type})Background music prompt not found: {structure.background_music.text}")
                    count += 1
        if count > 0:
            print(f"Background music prompt not found in {count} instances.")

    def get_asset_by_target_value(self, value: str) -> Optional[Asset]:
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
                            return asset
                    if _get_target_by_value(scene.narration.targets, value) is not None:
                        return scene.narration
                if _get_target_by_value(structure.background_music.targets, value) == value:
                    return structure.background_music
        return None

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
    def generate_short_story(premise, chapter_count=8) -> str:

        system_prompt = SYSTEM_PROMPT_SHORTS.format(story_schema=Story.model_json_schema())
        story: Story = generate_raw_story(
            model=Story, system_prompt=system_prompt, premise=premise, chapter_count=chapter_count
        )
        return story.save()

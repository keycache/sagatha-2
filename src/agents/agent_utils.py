import os
from typing import List, Optional

from pyexpat import model

from src.agents.agent_constants import AgentPath
from src.agents.response_models import StoryGeneratorResponseModel, StructuredStory, StructuredStoryAsset
from src.api_client import AssetResponse
from src.utils.file import get_files_with_prefix, make_directory, read_file, save_file
from src.utils.helper import save_base64_audio, save_base64_image, to_kebab_case


def get_random_story(raw_story_path: str = None) -> Optional[StoryGeneratorResponseModel]:
    if raw_story_path:
        content = read_file(raw_story_path)
        story = StoryGeneratorResponseModel.model_validate_json(content)
        return story
    for dirpath, dirnames, filenames in os.walk(AgentPath.STORY_GENERATOR):
        for filename in filenames:
            if filename.endswith(".json") and filename.startswith("1-raw-story-"):
                content = read_file(os.path.join(dirpath, filename))
                story = StoryGeneratorResponseModel.model_validate_json(content)
                return story
    return None


def get_random_structured_story(structured_story_path: str = None) -> Optional[StructuredStory]:
    if structured_story_path:
        content = read_file(structured_story_path)
        structured_story = StructuredStory.model_validate_json(content)
        return structured_story
    for dirpath, dirnames, filenames in os.walk(AgentPath.SCENE_BREAKDOWN_GENERATOR):
        for filename in filenames:
            if filename.endswith(".json") and filename.startswith("2-structured-story-"):
                content = read_file(os.path.join(dirpath, filename))
                structured_story = StructuredStory.model_validate_json(content)
                return structured_story
    return None


def get_random_structured_story_asset(
    structured_story_asset_path: str = None, aspect_ratio: str = "portrait"
) -> Optional[StructuredStoryAsset]:
    if structured_story_asset_path:
        content = read_file(structured_story_asset_path)
        structured_story = StructuredStoryAsset.model_validate_json(content)
        return structured_story
    for dirpath, dirnames, filenames in os.walk(AgentPath.STRUCTURED_STORY_ASSET):
        for filename in filenames:
            if filename.endswith(".json") and filename.startswith(f"3-structured-story-asset-{aspect_ratio}-"):
                content = read_file(os.path.join(dirpath, filename))
                structured_story = StructuredStoryAsset.model_validate_json(content)
                return structured_story
    return None


def save_story(
    story: StoryGeneratorResponseModel,
    file_path: str = None,
    mode="w",
    encoding="utf-8",
):
    if not file_path:
        name = to_kebab_case(story.title)
        base_dir = os.path.join(AgentPath.STORY_GENERATOR, name)
        make_directory(base_dir)
        file_path = os.path.join(base_dir, f"1-raw-story-{name}.json")
    print(f"Saving story to: {file_path}")
    return save_file(file_path, story.model_dump_json(indent=2), mode, encoding)


def save_scene_breakdown(structured_story: StructuredStory, file_path: str = None, mode="w", encoding="utf-8"):
    if not file_path:
        name = to_kebab_case(structured_story.title)
        base_dir = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, name)
        make_directory(base_dir)
        file_path = os.path.join(base_dir, f"2-structured-story-{name}.json")
    print(f"Saving structured_story to: {file_path}")
    return save_file(file_path, structured_story.model_dump_json(indent=2), mode, encoding)


def save_structured_story_asset(
    structured_story_asset: StructuredStoryAsset,
    aspect_ratio: str = "portrait",
    file_path: str = None,
    mode="w",
    encoding="utf-8",
):
    if not file_path:
        name = to_kebab_case(structured_story_asset.title)
        base_dir = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, name)
        make_directory(base_dir)
        file_path = os.path.join(base_dir, f"3-structured-story-asset-{aspect_ratio}-{name}.json")
    print(f"Saving structured_story_asset to: {file_path}")
    return save_file(file_path, structured_story_asset.model_dump_json(indent=2), mode, encoding)


def save_asset_image_reference(
    structured_story: StructuredStory,
    images: List[AssetResponse],
    aspect_ratio="portrait",
    model_name: str = "test",
):
    base_path = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, to_kebab_case(structured_story.title))
    assert os.path.exists(base_path)
    asset_base_path = os.path.join(base_path, "assets", aspect_ratio)
    make_directory(asset_base_path)
    image_paths = []
    for i, image_asset in enumerate(images, start=1):
        for j, item in enumerate(image_asset.data, start=1):
            name_attributes = [
                "imagereference",
                model_name,
                aspect_ratio,
                str(item.seed),
                image_asset.prompt,
            ]
            file_name = to_kebab_case(" ".join(name_attributes))
            image_path = save_base64_image(item.value, os.path.join(asset_base_path, f"{file_name}.png"))
            image_paths.append(image_path)
    return image_paths


def save_assets_images(
    structured_story: StructuredStory,
    images: List[AssetResponse],
    chapter: int,
    aspect_ratio="portrait",
    model_name: str = "test",
):
    base_path = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, to_kebab_case(structured_story.title))
    assert os.path.exists(base_path)
    asset_base_path = os.path.join(base_path, "assets", aspect_ratio, f"chapter-{chapter}")
    make_directory(asset_base_path)
    image_paths = []
    for i, image_asset in enumerate(images, start=1):
        for j, item in enumerate(image_asset.data, start=1):
            name_attributes = [
                "image",
                str(i),
                str(j),
                model_name,
                aspect_ratio,
                str(item.seed),
                image_asset.prompt,
            ]
            file_name = to_kebab_case(" ".join(name_attributes))
            image_path = save_base64_image(item.value, os.path.join(asset_base_path, f"{file_name}.png"))
            image_paths.append(image_path)
    return image_paths


def get_asset_base_path_for_music(structured_story: StructuredStory, chapter: int):
    base_path = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, to_kebab_case(structured_story.title))
    assert os.path.exists(base_path)
    return os.path.join(base_path, "assets", f"chapter-{chapter}")


def get_asset_base_path_for_image(structured_story: StructuredStory, chapter: int, aspect_ratio="portrait"):
    base_path = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, to_kebab_case(structured_story.title))
    assert os.path.exists(base_path)
    return os.path.join(base_path, "assets", aspect_ratio, f"chapter-{chapter}")


def save_assets_music(
    structured_story: StructuredStory,
    music_assets: List[AssetResponse],
    chapter: int,
    model_name: str = "test",
):
    base_path = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, to_kebab_case(structured_story.title))
    assert os.path.exists(base_path)
    asset_base_path = os.path.join(base_path, "assets", f"chapter-{chapter}")
    make_directory(asset_base_path)
    music_paths = []
    for i, image_asset in enumerate(music_assets, start=1):
        for j, item in enumerate(image_asset.data, start=1):
            name_attributes = [
                "music",
                str(i),
                str(j),
                model_name,
                str(item.seed),
                image_asset.prompt,
            ]
            file_name = to_kebab_case(" ".join(name_attributes))
            image_path = save_base64_audio(item.value, os.path.join(asset_base_path, f"{file_name}.mp3"))
            music_paths.append(image_path)
    return music_paths


def get_asset_base_path_for_narration(structured_story: StructuredStory, chapter: int):
    base_path = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, to_kebab_case(structured_story.title))
    assert os.path.exists(base_path)
    return os.path.join(base_path, "assets", f"chapter-{chapter}")


def save_assets_narration(
    structured_story: StructuredStory,
    narration_assets: List[AssetResponse],
    chapter: int,
    model_name: str = "test",
    format: str = "wav",
):
    base_path = os.path.join(AgentPath.SCENE_BREAKDOWN_GENERATOR, to_kebab_case(structured_story.title))
    assert os.path.exists(base_path)
    asset_base_path = os.path.join(base_path, "assets", f"chapter-{chapter}")
    make_directory(asset_base_path)
    narration_paths = []
    for i, image_asset in enumerate(narration_assets, start=1):
        for j, item in enumerate(image_asset.data, start=1):
            name_attributes = [
                "narration",
                str(i),
                str(j),
                model_name,
                str(item.seed),
                image_asset.prompt,
            ]
            file_name = to_kebab_case(" ".join(name_attributes))
            image_path = save_base64_audio(item.value, os.path.join(asset_base_path, f"{file_name}.{format}"))
            narration_paths.append(image_path)
    return narration_paths


def get_assets_paths_narration(
    structured_story: StructuredStory,
    chapter_number: int,
    scene_number: int,
):
    base_path = get_asset_base_path_for_narration(
        structured_story,
        chapter_number,
    )
    file_paths = get_files_with_prefix(base_path, f"narration-{scene_number}")
    return file_paths


def get_assets_paths_music(
    structured_story: StructuredStory,
    chapter_number: int,
    scene_number: int,
):
    base_path = get_asset_base_path_for_music(
        structured_story,
        chapter_number,
    )
    file_paths = get_files_with_prefix(base_path, f"music-{scene_number}")
    return file_paths


def get_assets_paths_image(
    structured_story: StructuredStory,
    chapter_number: int,
    scene_number: int,
    aspect_ratio="portrait",
):
    base_path = get_asset_base_path_for_image(structured_story, chapter_number, aspect_ratio)
    file_paths = get_files_with_prefix(base_path, f"image-{scene_number}")
    return file_paths


if __name__ == "__main__":
    structured_story = get_random_structured_story()
    out = get_assets_paths_image(structured_story, 1, 1, "portrait")
    print(out)

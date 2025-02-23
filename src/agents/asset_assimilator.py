from src.agents.agent_utils import (
    get_assets_paths_image,
    get_assets_paths_music,
    get_assets_paths_narration,
    get_random_structured_story,
    get_random_structured_story_asset,
    save_structured_story_asset,
)
from src.agents.response_models import AssetModel, AssetSceneModel, StructuredStory, StructuredStoryAsset
from src.utils.file import get_filename


def assimilate_assets(structured_story: StructuredStory, aspect_ratio: str = "portrait"):
    chapter_scenes_assets = []
    for chapter_number, chapter in enumerate(structured_story.scenes, start=1):
        asset_scene_models = []
        for scene_number, scene in enumerate(chapter, start=1):
            print(f"Processing assets for chapter {chapter_number} scene {scene_number}")
            asset_scene_model = AssetSceneModel()
            # Process narration assets
            assets_paths_narration = get_assets_paths_narration(structured_story, chapter_number, scene_number)
            narration_assets = []
            for asset_path in assets_paths_narration:
                asset_name_path = get_filename(asset_path)
                _, scene_number, variantion_count, model_name, seed, *_ = asset_name_path.split("-")
                print(f"Processing narration asset: {seed}, {asset_name_path}")
                narration_assets.append(
                    AssetModel(
                        path=asset_path,
                        seed=int(seed),
                        prompt=scene.narration_text,
                        model_name=model_name,
                    )
                )
            asset_scene_model.narration = narration_assets

            # Process music assets
            assets_paths_music = get_assets_paths_music(structured_story, chapter_number, scene_number)
            music_assets = []
            for asset_path in assets_paths_music:
                asset_name_path = get_filename(asset_path)
                _, scene_number, variantion_count, model_name, seed, *_ = asset_name_path.split("-")
                music_assets.append(
                    AssetModel(
                        path=asset_path,
                        seed=int(seed),
                        prompt=scene.music_prompt,
                        model_name=model_name,
                    )
                )
            asset_scene_model.music = music_assets

            # Process image assets
            assets_paths_image = get_assets_paths_image(structured_story, chapter_number, scene_number, aspect_ratio)
            image_assets = []
            for asset_path in assets_paths_image:
                asset_name_path = get_filename(asset_path)
                (
                    _,
                    scene_number,
                    variantion_count,
                    model_name,
                    aspect_ratio,
                    seed,
                    *_,
                ) = asset_name_path.split("-")
                image_assets.append(
                    AssetModel(
                        path=asset_path,
                        seed=int(seed),
                        prompt=scene.image_prompt,
                        model_name=model_name,
                    )
                )
            asset_scene_model.image = image_assets
            asset_scene_models.append(asset_scene_model)
        print(f"Chapter {chapter_number} assets assimilated. Number of asset_scene_models: {len(asset_scene_models)}")
        chapter_scenes_assets.append(asset_scene_models)
    structured_story_asset = StructuredStoryAsset(
        title=structured_story.title,
        chapters=structured_story.chapters,
        protogonist=structured_story.protogonist,
        characters=structured_story.characters,
        moral=structured_story.moral,
        chapter_scenes=chapter_scenes_assets,
    )
    ssa_path = save_structured_story_asset(structured_story_asset, aspect_ratio)
    return ssa_path


if __name__ == "__main__":
    # structured_story_asset = get_random_structured_story_asset(aspect_ratio="portrait")
    # print(structured_story_asset)
    path = r".data\stories\timmy-and-buster-a-tail-of-friendship\2-structured-story-timmy-and-buster-a-tail-of-friendship.json"
    structured_story: StructuredStory = get_random_structured_story(path)
    assimilate_assets(structured_story, aspect_ratio="portrait")

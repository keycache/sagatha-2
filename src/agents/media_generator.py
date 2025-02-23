import os
from typing import List

from moviepy import AudioFileClip, CompositeAudioClip, ImageClip, VideoClip, afx, concatenate_videoclips, vfx
from numpy import save

from src.agents.agent_constants import AgentPath
from src.agents.agent_utils import get_random_structured_story_asset
from src.agents.response_models import AssetModel, AssetSceneModel, StructuredStoryAsset
from src.constants import BACKGROUND_MUSIC_VOLUME, VIDEO_FPS
from src.utils.file import make_directory
from src.utils.helper import to_kebab_case


def save_scene(scene: AssetSceneModel, output_path: str) -> str:
    video = render_scene(scene)
    video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path


def render_scene(scene: AssetSceneModel) -> VideoClip:
    narration = get_asset_narration(scene.narration)
    image = get_asset_image(scene.image)
    music = get_asset_music(scene.music)

    print(f"Narration: {narration.path}\nImage: {image.path}\nMusic: {music.path}")
    narration_clip = AudioFileClip(narration.path)
    backgound_music_clip = AudioFileClip(music.path)
    image_clip = ImageClip(image.path)

    narration_duration = narration_clip.duration
    print(f"Narration duration: {narration_duration}")

    backgound_music_clip = backgound_music_clip.with_effects(
        [
            afx.AudioLoop(duration=narration_duration),
            afx.MultiplyVolume(BACKGROUND_MUSIC_VOLUME),
        ]
    )
    audio_clip = CompositeAudioClip([narration_clip, backgound_music_clip])
    audio_clip.with_effects([afx.AudioFadeIn(0.5), afx.AudioFadeOut(0.5)])

    image_clip = image_clip.with_fps(VIDEO_FPS).with_duration(narration_duration)
    video = image_clip.with_audio(audio_clip)
    video = video.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
    print("Writing video...", type(video))
    return video


def get_asset_narration(narration_assets: List[AssetModel]) -> AssetModel:
    return narration_assets[0]


def get_asset_image(image_assets: List[AssetModel]) -> AssetModel:
    return image_assets[0]


def get_asset_music(music_assets: List[AssetModel]) -> AssetModel:
    return music_assets[0]


def save_chapter_to_video(
    structured_story_asset: StructuredStoryAsset,
    chapter_scenes_video_clips: List[VideoClip],
    chapter_number: int,
    aspect_ratio: str = "portrait",
    codec: str = "libx264",
    audio_codec: str = "aac",
) -> str:

    kebab_title = to_kebab_case(structured_story_asset.title)
    base_path = os.path.join(
        AgentPath.VIDEO_OUTPUT,
        kebab_title,
        aspect_ratio,
    )
    make_directory(base_path)
    video_path = os.path.join(base_path, f"{chapter_number}-{kebab_title}.mp4")
    print(f"Saving video for chapter {chapter_number} to: {video_path}")
    concatenate_videoclips(chapter_scenes_video_clips).write_videofile(video_path, codec=codec, audio_codec=audio_codec)
    return video_path


def generate_video(structured_story_asset: StructuredStoryAsset, aspect_ratio: str = "portrait") -> str:
    chapter_video_paths = []
    for chapter_number, chapter in enumerate(structured_story_asset.chapter_scenes, start=1):
        scenes_video_clips = []
        for scene_number, scene in enumerate(chapter, start=1):
            video_clip = render_scene(scene)
            scenes_video_clips.append(video_clip)
        chapter_video_path = save_chapter_to_video(
            structured_story_asset, scenes_video_clips, chapter_number, aspect_ratio
        )
        chapter_video_paths.append(chapter_video_path)
    return chapter_video_paths


def test():
    # path = None
    path = r".data\stories\timmy-and-buster-a-tail-of-friendship\3-structured-story-asset-portrait-timmy-and-buster-a-tail-of-friendship.json"
    structured_story_asset: StructuredStoryAsset = get_random_structured_story_asset(
        structured_story_asset_path=path, aspect_ratio="portrait"
    )
    # out = structured_story_asset.chapter_scenes[0][0]
    # save_scene(out, ".data/test/test.mp4")
    generate_video(structured_story_asset)


if __name__ == "__main__":
    test()

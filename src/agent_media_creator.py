from httpx import get
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    VideoClip,
    afx,
    concatenate_audioclips,
    concatenate_videoclips,
    vfx,
)

from src.constants import (
    BACKGROUND_MUSIC_VOLUME,
    VIDEO_FPS,
    AspectRatio,
    AspectRatioDetails,
)
from src.models import Chapter, Scene, Story, Structure
from src.utils.helper import to_kebab_case


def get_structure_clip(structure: Structure, story: Story) -> VideoClip:
    print(f"Generating video for structure: {structure.type.name}")
    print(f"No. of scenes: {len(structure.scenes)}")
    music_target = story.get_active_target(structure.background_music)
    scenes_narration_clip = []
    scenes_image_clip = []
    for scene in structure.scenes:
        narration_target, images_targets = get_scene_targets(scene, story)
        print(f"No. words and images in the scene: {len(scene.narration.text.split(" "))} {len(images_targets)}")
        narration_clip = AudioFileClip(narration_target.value)
        scene_image_clips = [
            ImageClip(image.value)
            .with_duration(narration_clip.duration / len(images_targets))
            .with_fps(VIDEO_FPS)
            .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
            for image in images_targets
        ]
        scene_image_clip = concatenate_videoclips(scene_image_clips)
        scenes_narration_clip.append(narration_clip)
        scenes_image_clip.append(scene_image_clip)

    structure_narration_clip = concatenate_audioclips(scenes_narration_clip)
    backgound_music_clip = AudioFileClip(music_target.value)
    backgound_music_clip = backgound_music_clip.with_effects(
        [
            afx.AudioLoop(duration=structure_narration_clip.duration),
            afx.MultiplyVolume(BACKGROUND_MUSIC_VOLUME),
        ]
    )
    structure_audio_clip = CompositeAudioClip([structure_narration_clip, backgound_music_clip])
    structure_audio_clip.with_effects([afx.AudioFadeIn(0.5), afx.AudioFadeOut(0.5)])

    structure_image_clip = concatenate_videoclips(scenes_image_clip)
    structure_image_clip = structure_image_clip.with_fps(VIDEO_FPS).with_duration(structure_narration_clip.duration)

    structure_video = structure_image_clip.with_audio(structure_audio_clip)
    structure_video = structure_video.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])

    return structure_video


def get_chapter_clip(chapter: Chapter, story: Story, aspect_ratio: AspectRatioDetails) -> VideoClip:
    title = to_kebab_case(chapter.title)
    cover_image_path = story.get_cover_image_path(chapter, aspect_ratio=aspect_ratio)
    if not cover_image_path:
        raise ValueError(f"Cover image not found for chapter: {chapter.title}")
    intro_clip = ImageClip(cover_image_path).with_duration(1).with_fps(VIDEO_FPS)
    intro_file_path = f".data/video/{title}-intro.mp4"
    render_video(intro_clip, intro_file_path)
    out_file_paths = [intro_file_path]
    for structure in chapter.structures:
        print(f"Generating video for structure: {structure.type.value}")
        structure_clip = get_structure_clip(structure, story)
        file_name = f".data/video/{to_kebab_case(chapter.title)}-{structure.type.value}.mp4"
        render_video(structure_clip, file_name)
        out_file_paths.append(file_name)
    # chapter_clips = [get_structure_clip(structure, story) for structure in chapter.structures]
    # chapter_clip = concatenate_videoclips(chapter_clips)
    # print(f"Chapter video duration: {chapter_clip.duration}")

    # return concatenate_videoclips([intro_clip, chapter_clip])
    return out_file_paths


def get_scene_targets(scene: Scene, story: Story) -> VideoClip:
    narration_target = story.get_active_target(scene.narration)
    images_targets = [story.get_active_target(image) for image in scene.image]
    return narration_target, images_targets


def render_video(clip: VideoClip, output_path: str, codec="libx264", audio_codec="aac") -> None:
    clip.write_videofile(output_path, codec=codec, audio_codec=audio_codec)
    return output_path


if __name__ == "__main__":
    import json

    path = ".data/story/pistan-and-the-mystery-of-the-shimmering-feathers/pistan-and-the-mystery-of-the-shimmering-feathers.json"
    with open(path, "r") as file:
        data = json.load(file)
        story = Story.model_validate(data)
    # clip = get_structure_clip(structure=story.chapters[0].structures[0], story=story)
    clip = get_chapter_clip(chapter=story.chapters[0], story=story, aspect_ratio=AspectRatio.AR_9_16)
    # render_video(clip, ".data/video/test.mp4")

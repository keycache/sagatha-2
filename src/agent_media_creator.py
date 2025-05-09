import os
import subprocess
import tempfile
from typing import List

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    VideoClip,
    VideoFileClip,
    afx,
    concatenate_audioclips,
    concatenate_videoclips,
    vfx,
)

from src.constants import BACKGROUND_MUSIC_VOLUME, VIDEO_FPS, AspectRatio, AspectRatioDetails
from src.models import Chapter, Scene, Story, Structure
from src.utils.helper import to_kebab_case


def get_base_video_path_for_story(story: Story) -> str:
    return os.path.join(".data/story", to_kebab_case(story.title))


def create_temp_file(file_paths: List[str]) -> str:
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as temp_file:
            content = "\n".join([f"file {file_path}" for file_path in file_paths])
            temp_file.write(content)
            return temp_file.name
    finally:
        # Make sure to close the file so it's saved properly
        temp_file.close()


def create_chapter_videos(chapter: Chapter, story: Story, aspect_ratio: AspectRatioDetails) -> str:
    video_paths = []
    base_video_path = get_base_video_path_for_story(story)
    for i, story_chapter in enumerate(story.chapters):
        if chapter and story_chapter != chapter:
            continue
        print("-----------------------------------------------------------")
        print(f"Generating video for chapter: {story_chapter.chapter_number}-{story_chapter.title}")
        chapter_title = to_kebab_case(story_chapter.title)
        chapter_video_folder = f"{base_video_path}/{story_chapter.chapter_number}-{chapter_title}/{aspect_ratio.mode}"
        intro_video_path = create_intro_video(story_chapter, story, aspect_ratio)
        out_file_paths = [os.path.abspath(intro_video_path)] if intro_video_path else []

        for structure in story_chapter.structures:
            print(f"Generating video for structure: {structure.type.value}")
            structure_clip = get_structure_clip(structure, story)
            file_name = f"{chapter_video_folder}/{structure.type.value}.mp4"
            render_video(structure_clip, file_name)
            out_file_paths.append(os.path.abspath(file_name))
        structures_video_file_path = create_temp_file(out_file_paths)
        chapter_video_file_path = f"{chapter_video_folder}/{chapter_title}.mp4"
        print(f"Structures video file path: {structures_video_file_path}")
        print(f"All video file paths: {out_file_paths}")

        command = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            structures_video_file_path,
            "-c",
            "copy",
            "-y",
            chapter_video_file_path,
        ]

        # Run the command
        print("Generating chapter video. Running ffmpeg...")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            print(f"Error generating narration: {result.stderr}")
            raise ValueError(f"Error generating video for chapter: {story_chapter.title}")
        else:
            print(f"Chapter video generated successfully: {chapter_video_file_path}")
            post_process_video(chapter_video_file_path, aspect_ratio)
            story.add_resource(chapter, aspect_ratio, chapter_video_file_path)
            video_paths.append(chapter_video_file_path)
        print("-----------------------------------------------------------")
    return video_paths


def create_intro_video(chapter: Chapter, story: Story, aspect_ratio: AspectRatioDetails) -> str:
    # print(f"Generating intro video for chapter: {chapter.title}")
    chapter_title = to_kebab_case(chapter.title)
    base_video_path = get_base_video_path_for_story(story)
    chapter_video_folder = f"{base_video_path}/{chapter.chapter_number}-{chapter_title}/{aspect_ratio.mode}"
    intro_video_path = f"{chapter_video_folder}/0-intro.mp4"
    cover_image_path = story.get_cover_image_path(chapter, aspect_ratio=aspect_ratio)
    if not cover_image_path:
        raise ValueError(f"Cover image not found for chapter: {chapter.title}")
    command = [
        "ffmpeg",
        "-loop",
        "1",
        "-i",
        cover_image_path,
        "-f",
        "lavfi",
        "-t",
        "2",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest",
        "-vf",
        f"scale={aspect_ratio.width}:{aspect_ratio.height},fps={VIDEO_FPS}",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        intro_video_path,
        "-y",
    ]
    # Run the command
    # print("Generating intro video...")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        print(f"Error generating narration: {result.stderr}")
    else:
        print(f"Chapter intro video generated successfully: {intro_video_path}")
        return intro_video_path
    return None


def get_structure_clip(structure: Structure, story: Story) -> VideoClip:
    music_target = story.get_active_target(structure.background_music)
    scenes_narration_clip = []
    scenes_image_clip = []
    for scene in structure.scenes:
        narration_target, images_targets = get_scene_targets(scene, story)
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


def get_scene_targets(scene: Scene, story: Story) -> VideoClip:
    narration_target = story.get_active_target(scene.narration)
    images_targets = [story.get_active_target(image) for image in scene.image]
    return narration_target, images_targets


def render_video(clip: VideoClip, output_path: str, codec="libx264", audio_codec="aac") -> str:
    clip.write_videofile(output_path, codec=codec, audio_codec=audio_codec)
    return output_path


def post_process_video(video_path: str, aspect_ratio_details: AspectRatioDetails):
    video_file_clip = VideoFileClip(video_path)
    speed_factor = video_file_clip.duration / aspect_ratio_details.duration
    if speed_factor > 1:
        temp_path = f"{video_path.replace('.mp4', '-adjusted.mp4')}"
        command = [
            "ffmpeg",
            "-i",
            video_path,
            "-filter_complex",
            f"[0:v]setpts=PTS/{speed_factor}[v];[0:a]atempo={speed_factor}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            temp_path,
            "-y",
        ]
        # Run the command
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            print(f"Error postprocessing the file: {result.stderr}")
        else:
            os.replace(temp_path, video_path)
            print(f"Video generated successfully: {video_path}")

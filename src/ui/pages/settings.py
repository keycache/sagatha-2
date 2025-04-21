import streamlit as st

from src.constants import AspectRatio
from src.models import Settings
from src.styles import ImageStyle
from src.ui.constants import Key
from src.ui.utils import get_settings


def update_video_settings(key: str):
    settings: Settings = get_settings()
    if key == Key.VS_FRAME_RATE:
        settings.video.frame_rate = st.session_state[key]
    settings.save()


def update_audio_settings(key: str):
    settings: Settings = get_settings()
    if key == Key.AS_BG_MUSIC_VOLUME_FACTOR:
        settings.audio.bg_music_factor = st.session_state[key]
    settings.save()


def update_image_settings(key: str):
    settings: Settings = get_settings()
    if key == Key.IS_IMAGE_STYLE:
        settings.image.image_style = ImageStyle[st.session_state[key]]
    elif key == Key.ASPECT_RATIO:
        settings.image.aspect_ratio = st.session_state[key]
    settings.save()


def update_story_settings(key: str):
    settings: Settings = get_settings()
    if key == Key.SS_CHAPTER_COUNT:
        settings.story.chapter_count = st.session_state[key]
    settings.save()


def render_settings():
    settings: Settings = get_settings()
    ar_modes = AspectRatio().get_modes()

    st.title("Settings")
    st.divider()
    st.subheader("Video")
    st.selectbox(
        "Frame Rate",
        options=[24, 30, 60],
        index=[24, 30, 60].index(settings.video.frame_rate),
        key=Key.VS_FRAME_RATE,
        on_change=update_video_settings,
        kwargs={"key": Key.VS_FRAME_RATE},
    )
    st.divider()
    st.subheader("Audio")
    st.slider(
        "Background Music Volume Factor",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        format="%.2f",
        help="Volume factor for background music.",
        value=settings.audio.bg_music_factor,
        key=Key.AS_BG_MUSIC_VOLUME_FACTOR,
        on_change=update_audio_settings,
        kwargs={"key": Key.AS_BG_MUSIC_VOLUME_FACTOR},
    )
    st.divider()
    st.subheader("Image")
    st.selectbox(
        "Image Style",
        options=[style.name for style in ImageStyle],
        index=[style.name for style in ImageStyle].index(settings.image.image_style.name),
        key=Key.IS_IMAGE_STYLE,
        on_change=update_image_settings,
        kwargs={"key": Key.IS_IMAGE_STYLE},
    )
    st.radio(
        "Aspect Ratio",
        options=ar_modes,
        index=ar_modes.index(settings.image.aspect_ratio),
        key=Key.ASPECT_RATIO,
        on_change=update_image_settings,
        kwargs={"key": Key.ASPECT_RATIO},
        horizontal=True,
        help="Aspect ratio for the to be generated images.",
    )
    st.divider()
    st.subheader("Story")
    chapter_count_options = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    st.selectbox(
        "Default Chapters Count",
        options=chapter_count_options,
        index=chapter_count_options.index(settings.story.chapter_count),
        help="Default number of chapters for the story.",
        key=Key.SS_CHAPTER_COUNT,
        on_change=update_story_settings,
        kwargs={"key": Key.SS_CHAPTER_COUNT},
    )


render_settings()

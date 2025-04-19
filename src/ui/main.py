from re import S

import streamlit as st
from httpx import get

from src.constants import AspectRatioDetails
from src.models import Chapter, Story
from src.ui.utils import (
    activate_target,
    get_aspect_ratio_map,
    get_chapters_map,
    get_cover_images_targets,
    get_key,
    get_stories_map,
    set_key,
)

st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)


class Constants:
    COVER_IMAGES = "Cover Images"
    GENERATE_STORY = "Generate Story"
    INSPECT_STORY = "Inspect Story"


class Key:
    COVER_IMAGES = "cover_images"
    STORY_MAP = "story_map"
    STORY_NAME = "story_name"
    CHAPTER_NAME = "chapter_name"
    COVER_IMAGE_SELECT = "cover_image_select"
    ASPECT_RATIO = "aspect_ratio"
    ASPECT_RATIO_MAP = "aspect_ratio_map"
    STORY_PREMISE = "story_premise"
    STORY_CHAPTER_COUNT = "story_chapter_count"


SIDEBAR_OPTIONS = [Constants.COVER_IMAGES, Constants.GENERATE_STORY, Constants.INSPECT_STORY]


def render_sidebar():
    story_map = get_key(Key.STORY_MAP)
    aspect_ratio_map = get_key(Key.ASPECT_RATIO_MAP)
    if aspect_ratio_map is None:
        aspect_ratio_map = get_aspect_ratio_map()
        set_key(Key.ASPECT_RATIO_MAP, aspect_ratio_map)
    if story_map is None:
        # Load stories map only once
        story_map = get_stories_map()
        set_key(Key.STORY_MAP, story_map)
    st.sidebar.selectbox("Select a story", list(story_map.keys()), key=Key.STORY_NAME)
    st.sidebar.selectbox("Select an option", SIDEBAR_OPTIONS, key=Key.COVER_IMAGES)
    st.sidebar.radio("Select Aspect Ratio", list(aspect_ratio_map.keys()), key=Key.ASPECT_RATIO)


def render_cover_images():
    def handle_generate_cover_image(**kwargs):
        chapter: Chapter = kwargs["chapter"]
        story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
        aspect_ratio = get_key(Key.ASPECT_RATIO_MAP)[get_key(Key.ASPECT_RATIO)]
        story.generate_cover_image(chapter, aspect_ratio, force=True)
        stories_map = get_stories_map()
        set_key(Key.STORY_MAP, stories_map)

    def handle_check(*args, **kwargs):
        index, targets, story = kwargs["index"], kwargs["targets"], get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
        targets = activate_target(targets, index)
        story.save()

    st.title(get_key(Key.STORY_NAME))
    chapters_cover_images_targets = get_cover_images_targets(get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)])
    selected_chapter = st.radio(
        "Select a chapter for cover",
        list(chapters_cover_images_targets.keys()),
        key=Key.CHAPTER_NAME,
        horizontal=True,
    )
    story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
    chapter: Chapter = get_chapters_map(story)[selected_chapter]
    aspect_ratio: AspectRatioDetails = get_key(Key.ASPECT_RATIO_MAP)[get_key(Key.ASPECT_RATIO)]
    ref_cover_image_path = story.get_reference_cover_image(chapter, aspect_ratio)
    selected_chapter = get_key(Key.CHAPTER_NAME)
    col1, col2 = st.columns([10, 2])
    col1.header(f"Cover Image for Chapter: {selected_chapter}")
    col2.button(
        "Generate New Cover",
        on_click=handle_generate_cover_image,
        type="primary",
        kwargs={"chapter": get_chapters_map(get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)])[selected_chapter]},
    )

    targets = chapters_cover_images_targets[selected_chapter]
    if not targets:
        st.warning("No cover images available for this chapter.")
        return
    with st.container():
        for i, col in enumerate(st.columns(len(targets))):
            with col:
                st.image(targets[i].value, width=300)
                st.checkbox(
                    " ",
                    value=targets[i].active,
                    key=f"checkbox_{i}",
                    on_change=handle_check,
                    kwargs={"index": i, "targets": targets},
                    disabled=len(targets) <= 1,
                )
    cover_image_prompt = chapter.get_cover_image_prompt(
        protagonist=story.protagonist,
        aspect_ratio=aspect_ratio,
        ref_cover_image_available=bool(ref_cover_image_path),
    )
    st.markdown("### Cover Image Prompt")
    st.markdown(f"`{cover_image_prompt}`")


def render_generate_story():
    st.title("Generate Story")

    st.text_area("Story Premise", placeholder="Write your story premise here...", key=Key.STORY_PREMISE)
    st.number_input("Number of Chapters", min_value=2, max_value=10, value=2, key=Key.STORY_CHAPTER_COUNT)

    aspect_ratio: AspectRatioDetails = get_key(Key.ASPECT_RATIO_MAP)[get_key(Key.ASPECT_RATIO)]

    if st.button("Generate Story", type="primary"):
        if aspect_ratio.mode == "portrait":
            premise = get_key(Key.STORY_PREMISE)
            chapter_count = get_key(Key.STORY_CHAPTER_COUNT)
            path = Story.generate_short_story(premise=premise, chapter_count=chapter_count)
            st.toast(f"Story generated at: {path}")
            get_stories_map()
            set_key(Key.STORY_MAP, get_stories_map())


def render_inspect_story():
    story_map = get_key(Key.STORY_MAP)
    if story_map is None:
        st.warning("No stories available to inspect.")
        return
    selected_story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
    chapters_map = get_chapters_map(selected_story)
    st.title(f"Inspect Story: {selected_story.title}")
    st.radio(
        "Select a chapter to inspect",
        list(chapters_map.keys()),
        key=Key.CHAPTER_NAME,
        horizontal=True,
    )
    selected_chapter: Chapter = chapters_map[get_key(Key.CHAPTER_NAME)]
    word_count = selected_chapter.get_word_count()
    st.markdown(f"### Word Count: {word_count}")
    for i, structure in enumerate(selected_chapter.structures):
        st.markdown(f"### {structure.type.upper()}")
        for j, scene in enumerate(structure.scenes):
            # st.text_area(label=f"Scene {j+1}", value=scene.narration.text, key=f"scene_{i}_{j}")
            st.write(scene.narration.text, key=f"scene_{i}_{j}")


def render():
    render_sidebar()
    sidebar_option = get_key(Key.COVER_IMAGES)
    if sidebar_option == Constants.COVER_IMAGES:
        render_cover_images()
    elif sidebar_option == Constants.GENERATE_STORY:
        render_generate_story()
    elif sidebar_option == Constants.INSPECT_STORY:
        render_inspect_story()


if __name__ == "__main__":
    render()

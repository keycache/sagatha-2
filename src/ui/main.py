import pandas as pd
import pyperclip
import streamlit as st

from src.constants import AspectRatioDetails
from src.models import Asset, Chapter, Story, Structure
from src.styles import ImageStyle
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
    ALL = "All"
    COVER_IMAGES = "Cover Images"
    GENERATE_STORY = "Generate Story"
    INSPECT_STORY = "Inspect Story"
    SCENE_IMAGES = "Scene Images"
    BG_MUSIC = "Background Music"
    NARRATION = "Narration"
    VALIDATE_ASSETS = "Validate Assets"


SIDEBAR_OPTIONS = [
    Constants.GENERATE_STORY,
    Constants.INSPECT_STORY,
    Constants.COVER_IMAGES,
    Constants.SCENE_IMAGES,
    Constants.BG_MUSIC,
    Constants.NARRATION,
    Constants.VALIDATE_ASSETS,
]


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
    SCENE_IMAGES_STRUCTURE_SELECT = "scene_images_structure_select"
    VALIDATE_ASSET = "validate_asset"


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


def render_scene_images():
    def handle_generate_cover_image(**kwargs):
        asset: Asset = kwargs["asset"]
        chapter: Chapter = kwargs["chapter"]
        story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
        if asset is None:
            st.toast("No image available for this structure.")
            return
        # print(f"Generating image for asset: {asset} and chapter: {chapter.title}")
        aspect_ratio: AspectRatioDetails = get_key(Key.ASPECT_RATIO_MAP)[get_key(Key.ASPECT_RATIO)]
        image_path = story.generate_image(
            asset, chapter, aspect_ratio=aspect_ratio, style=ImageStyle.STORY_BOOK_CLASSIC, force=True
        )
        st.toast(f"Image generated at: {image_path}")
        set_key(Key.STORY_MAP, get_stories_map())

    def handle_check(**kwargs):
        index, targets, story = kwargs["index"], kwargs["targets"], get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
        print(f"Checkbox clicked for index: {index}, targets: {len(targets)}")
        targets = activate_target(targets, index)
        story.save()

    def get_image_prompt(image_asset: Asset):
        aspect_ratio: AspectRatioDetails = get_key(Key.ASPECT_RATIO_MAP)[get_key(Key.ASPECT_RATIO)]
        image_prompt = chapter.get_image_prompt(
            image_asset.text, aspect_ratio=aspect_ratio, style=ImageStyle.STORY_BOOK_CLASSIC
        )
        return image_prompt

    story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
    chapters_map = get_chapters_map(story)
    st.title(f"Scene Images: {story.title}")
    selected_chapter = st.radio(
        "Select a chapter for scene images",
        list(chapters_map.keys()),
        key=Key.CHAPTER_NAME,
        horizontal=True,
    )
    chapter: Chapter = chapters_map[selected_chapter]
    structures_col, scenes_col = st.columns([3, 9])
    with structures_col:
        st.header("Structures")
        structure_names = [structure.type.value for structure in chapter.structures]
        st.radio(
            "Select a structure",
            structure_names,
            key=Key.SCENE_IMAGES_STRUCTURE_SELECT,
            horizontal=False,
        )

    with scenes_col:
        st.header("Scenes")
        selected_structure = get_key(Key.SCENE_IMAGES_STRUCTURE_SELECT)
        structure: Structure = chapter.get_structure(selected_structure)
        for i, scene in enumerate(structure.scenes):
            for j, image in enumerate(scene.image):
                targets = image.targets
                col1, col2 = st.columns([9, 3])
                col1.header(f"Scene {i + 1} - Image {j + 1}")
                col2.button(
                    "Generate New Image",
                    type="primary",
                    key=f"generate_image_{i}_{j}",
                    on_click=handle_generate_cover_image,
                    kwargs={"asset": image, "chapter": chapter},
                )

                if targets:
                    with st.container():
                        for k, col in enumerate(st.columns(len(targets))):
                            with col:
                                st.image(targets[k].value, width=300)
                                st.checkbox(
                                    " ",
                                    value=targets[k].active,
                                    key=f"checkbox_{i}_{j}_{k}",
                                    on_change=handle_check,
                                    kwargs={"index": k, "targets": targets},
                                    disabled=len(targets) <= 1,
                                )
                                st.button(
                                    ":clipboard:",
                                    key=f"copy_{i}_{j}_{k}",
                                    on_click=pyperclip.copy,
                                    args=(targets[k].value,),
                                )
                else:
                    st.warning("No images available for this scene.")
                with st.expander("Image Prompt", expanded=False):
                    image_prompt = get_image_prompt(image)
                    st.markdown("### Image Prompt")
                    st.code(image_prompt, wrap_lines=True)


def render_cover_images():
    def handle_generate_cover_image(**kwargs):
        chapter: Chapter = kwargs["chapter"]
        story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
        aspect_ratio = get_key(Key.ASPECT_RATIO_MAP)[get_key(Key.ASPECT_RATIO)]
        story.generate_cover_image(chapter, aspect_ratio, style=ImageStyle.STORY_BOOK_CLASSIC, force=True)
        stories_map = get_stories_map()
        set_key(Key.STORY_MAP, stories_map)

    def handle_check(*args, **kwargs):
        index, targets, story = kwargs["index"], kwargs["targets"], get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
        targets = activate_target(targets, index)
        story.save()

    st.title(f"Cover Images: {get_key(Key.STORY_NAME)}")
    chapters_cover_images_targets = get_cover_images_targets(get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)])
    selected_chapter = st.radio(
        "Select a chapter for cover images assets",
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
                st.button(":clipboard:", key=f"copy_{i}", on_click=pyperclip.copy, args=(targets[i].value,))
    cover_image_prompt = chapter.get_cover_image_prompt(
        aspect_ratio=aspect_ratio,
        ref_cover_image_available=bool(ref_cover_image_path),
        style=ImageStyle.STORY_BOOK_CLASSIC,
    )
    with st.expander("Cover Image Prompt", expanded=False):
        st.code(cover_image_prompt, wrap_lines=True)


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
            st.write(scene.narration.text)


def render_background_music():
    st.title(f"Background Music: {get_key(Key.STORY_NAME)}")
    chapters_map = get_chapters_map(get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)])
    selected_chapter = st.radio(
        "Select a chapter for bg music assets",
        list(chapters_map.keys()),
        key=Key.CHAPTER_NAME,
        horizontal=True,
    )
    story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
    chapter: Chapter = get_chapters_map(story)[selected_chapter]
    for i, structure in enumerate(chapter.structures):
        col1, col2 = st.columns([9, 3])
        col1.markdown(f"### {structure.type.upper()}")
        col2.button(
            "Generate New BG Music",
            type="primary",
            key=f"generate_bg_music_{i}",
            on_click=story.generate_background_music,
            kwargs={"chapter_index": chapter.chapter_number - 1},
        )
        if structure.background_music.targets is not None:
            for j, target in enumerate(structure.background_music.targets):
                col1, col2 = st.columns([9, 3])
                col1.audio(target.value, format="audio/wav")
                col2.button(":clipboard:", key=f"copy_{i}_{j}", on_click=pyperclip.copy, args=(target.value,))
        st.markdown("#### Background Music Prompt")
        st.code(wrap_lines=True, body=structure.background_music.text)
        st.divider()


def render_narration():
    story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
    chapters_map = get_chapters_map(story)
    st.title(f"Narration: {story.title}")
    selected_chapter = st.radio(
        "Select a chapter for narration assets",
        list(chapters_map.keys()),
        key=Key.CHAPTER_NAME,
        horizontal=True,
    )
    chapter: Chapter = chapters_map[selected_chapter]
    for i, structure in enumerate(chapter.structures):
        st.markdown(f"### {structure.type.upper()}")
        for j, scene in enumerate(structure.scenes):
            col1, col2 = st.columns([9, 3])
            col1.markdown(f"#### Scene {j + 1}")
            col2.button(
                "Generate New Narration",
                type="primary",
                key=f"generate_narration_{i}_{j}",
                on_click=story.generate_narration,
                kwargs={"narration": scene.narration, "chapter": chapter},
            )
            if scene.narration.targets is not None:
                for k, target in enumerate(scene.narration.targets):
                    col1, col2 = st.columns([9, 3])
                    col1.audio(target.value, format="audio/wav")
                    col2.button(":clipboard:", key=f"copy_{i}_{j}_{k}", on_click=pyperclip.copy, args=(target.value,))
            st.markdown("#### Narration Prompt")
            st.code(wrap_lines=True, body=scene.narration.text)
        st.divider()


def render_validate_assets():
    story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
    chapters_map = get_chapters_map(story)
    st.title(f"Validate Assets: {story.title}")
    selected_chapter = st.radio(
        "Select a chapter for narration assets",
        list(chapters_map.keys()) + [Constants.ALL],
        key=Key.CHAPTER_NAME,
        horizontal=True,
    )
    OPTIONS = [Constants.COVER_IMAGES, Constants.SCENE_IMAGES, Constants.BG_MUSIC, Constants.NARRATION, Constants.ALL]
    chapter: Chapter = chapters_map[selected_chapter] if selected_chapter != Constants.ALL else None
    chapter_index = chapter.chapter_number - 1 if chapter else None
    st.segmented_control(
        "Select an option to validate",
        OPTIONS,
        key=Key.VALIDATE_ASSET,
        selection_mode="single",
    )
    selected_option = get_key(Key.VALIDATE_ASSET)
    missing = []
    if selected_option == Constants.COVER_IMAGES:
        missing = story.validate_cover_image(chapter_index=chapter_index)
    elif selected_option == Constants.SCENE_IMAGES:
        missing = story.validate_images(chapter_index=chapter_index)
    elif selected_option == Constants.BG_MUSIC:
        missing = story.validate_background_music(chapter_index=chapter_index)
    elif selected_option == Constants.NARRATION:
        missing = story.validate_narration(chapter_index=chapter_index)
    elif selected_option == Constants.ALL:
        missing_assets = story.validate_assets(chapter_index=chapter_index)
        print("Missing assets:", missing_assets)
        for asset_type, missing in missing_assets.items():
            if missing:
                with st.expander(f"**Missing {asset_type}**"):
                    df = pd.DataFrame(missing)
                    st.table(df)
        return

    if missing:
        df = pd.DataFrame(missing)
        st.table(df)
    elif selected_option is not None:
        st.toast(f"{selected_option}:No missing assets found.")


def render():
    render_sidebar()
    sidebar_option = get_key(Key.COVER_IMAGES)
    if sidebar_option == Constants.COVER_IMAGES:
        render_cover_images()
    elif sidebar_option == Constants.GENERATE_STORY:
        render_generate_story()
    elif sidebar_option == Constants.INSPECT_STORY:
        render_inspect_story()
    elif sidebar_option == Constants.SCENE_IMAGES:
        render_scene_images()
    elif sidebar_option == Constants.BG_MUSIC:
        render_background_music()
    elif sidebar_option == Constants.NARRATION:
        render_narration()
    elif sidebar_option == Constants.VALIDATE_ASSETS:
        render_validate_assets()


if __name__ == "__main__":
    render()

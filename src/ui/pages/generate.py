import streamlit as st

from src.agent_media_creator import create_chapter_videos
from src.models import Chapter, Story
from src.ui.constants import Constants, Key
from src.ui.utils import get_chapters_map, get_key, get_settings_ardetails, get_stories_map, set_key


def render():
    st.write("# Generate")
    st.write("This is the generate page.")

    story_map = get_key(Key.STORY_MAP)
    if story_map is None:
        # Load stories map only once
        story_map = get_stories_map()
        set_key(Key.STORY_MAP, story_map)
    st.selectbox("Select a story", list(story_map.keys()), key=Key.STORY_NAME)

    story: Story = get_key(Key.STORY_MAP)[get_key(Key.STORY_NAME)]
    if not story:
        st.warning("No story selected.")
        return

    chapters_map = get_chapters_map(story)

    selected_chapter = st.radio(
        "Select a chapter for assets validation",
        list(chapters_map.keys()) + [Constants.ALL],
        key=Key.CHAPTER_NAME,
        horizontal=True,
    )

    # OPTIONS = [Constants.COVER_IMAGES, Constants.SCENE_IMAGES, Constants.BG_MUSIC, Constants.NARRATION, Constants.ALL]
    chapter: Chapter = chapters_map[selected_chapter] if selected_chapter != Constants.ALL else None
    chapter_index = chapter.chapter_number - 1 if chapter else None

    missing_assets = story.validate_assets(chapter_index=chapter_index)
    missing = any([bool(value) for _, value in missing_assets.items()])
    print(f"Missing assets: {missing_assets}")
    print(f"Missing: {missing}")
    message = (
        "Generate video for the selected chapter"
        if not missing
        else "Some assets are missing. Please validate them before generating the video."
    )
    if st.button("Generate Video", type="primary", disabled=missing, help=message):
        create_chapter_videos(chapter=chapter, story=story, aspect_ratio=get_settings_ardetails())


render()

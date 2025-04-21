import streamlit as st

from src.constants import AspectRatioDetails
from src.models import Story
from src.ui.constants import Key
from src.ui.utils import get_key, get_settings_ardetails, get_settings_chapter_count, get_stories_map, set_key

st.title("Generate Story")

st.text_area("Story Premise", placeholder="Write your story premise here...", key=Key.STORY_PREMISE)
st.number_input(
    "Number of Chapters",
    min_value=2,
    max_value=10,
    value=get_settings_chapter_count(),
    key=Key.STORY_CHAPTER_COUNT,
)

aspect_ratio: AspectRatioDetails = get_settings_ardetails()

if st.button("Generate Story", type="primary"):
    if aspect_ratio.mode == "portrait":
        premise = get_key(Key.STORY_PREMISE)
        chapter_count = get_key(Key.STORY_CHAPTER_COUNT)
        path = Story.generate_short_story(premise=premise, chapter_count=chapter_count)
        st.toast(f"Story generated at: {path}")
        get_stories_map()
        set_key(Key.STORY_MAP, get_stories_map())

import json
import os
from typing import Dict, List, Optional

import streamlit as st

from src.constants import AspectRatio, AspectRatioDetails
from src.models import Asset, Chapter, Story, Target


def get_key(key, default=None):
    return st.session_state.get(key, default)


def set_key(key, value):
    st.session_state[key] = value
    return value


def get_stories_paths(base_path: str = ".data/story") -> list[str]:
    story_paths = []
    for item in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, item)):
            base_story_path = os.path.join(base_path, item)
            story_path = os.path.join(base_story_path, f"{item}.json")
            print(f"Checking story path: {story_path}")
            if os.path.exists(story_path):
                story_paths.append(story_path)
            else:
                print(f"Story path not found: {story_path}")
    return story_paths


def get_story(story_path: str) -> Story:
    print(f"Loading story from path: {story_path}")
    with open(story_path, "r") as f:
        data = json.load(f)
        return Story.model_validate(data)


def get_stories_map(base_path: str = ".data/story") -> dict[str, Story]:
    stories_path = get_stories_paths(base_path)
    stories_map = {}
    for story_path in stories_path:
        story = get_story(story_path)
        stories_map[story.title] = story
    return stories_map


def get_chapters_map(story: Story) -> dict[str, Chapter]:
    chapters_map = {}
    for chapter in story.chapters:
        chapters_map[chapter.title] = chapter
    return chapters_map


def get_aspect_ratio_map() -> dict[str, AspectRatioDetails]:
    return {
        AspectRatio.AR_9_16.mode: AspectRatio.AR_9_16,
        AspectRatio.AR_16_9.mode: AspectRatio.AR_16_9,
        AspectRatio.AR_1_1.mode: AspectRatio.AR_1_1,
    }


def get_cover_images_targets(story: Story, name: str = "") -> Dict[str, List[Target]]:
    chapters_assets = {}
    chapters_map = get_chapters_map(story)
    for chapter_name, chapter in chapters_map.items():
        if name and chapter_name != name:
            continue
        chapters_assets[chapter_name] = chapter.cover_image.targets
    return chapters_assets


def get_active_target(targets: List[Target]) -> Optional[int]:
    for i, obj in enumerate(targets):
        if getattr(obj, "active", False):
            return i
    return None


def activate_target(targets: List[Target], index: int):
    for i, target in enumerate(targets):
        if i == index:
            target.active = True
        else:
            target.active = False
    return targets

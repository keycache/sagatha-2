from typing import List

from phi.agent import Agent
from phi.model.google import Gemini
from pydantic import BaseModel, Field

from src.agents.agent_constants import STORY_GENERATOR_INSTRUCTIONS, STORY_GENERATOR_SYSTEM_PROMPT, AspectRatio
from src.agents.agent_utils import get_random_story, get_random_structured_story, save_story, save_structured_story
from src.agents.base import BaseAgent
from src.agents.response_models import Character, SceneModel, StoryGeneratorResponseModel, StructuredStory
from src.constants import MODEL_NAME


class Scene(BaseModel):
    narration_text: str = Field(
        ...,
        title="The scene's narrative text, composed of up to 3 sentences that capture a distinct segment of the chapter.",
    )
    image_prompt: str = Field(
        ...,
        title="A descriptive prompt suitable for a text-to-image generator that captures the visual essence of the scene. Includes the protagonist's age physical attributes and clothing. Other secondary charaters can be present, but the prompt should have enough information about thir physical appearance, clothing(if applicable), and other details to generate a realistic image. If the secondary characters are animals, include the breed, color, and any other relevant information about their physical appearance. Do not include the names of the charaters, but include the physical looks and description of the charaters",
    )
    music_prompt: str = Field(
        ..., title="A descriptive prompt for generating background music that matches the scene's mood and tone."
    )


class Chapter(BaseModel):
    title: str = Field(..., title="The title of the chapter")
    scenes: List[Scene] = Field(
        ..., title="List of scenes for a given chapter. Every chapter should have atleast 20 scenes."
    )


class StructuredStoryResponseModel(BaseModel):
    title: str = Field(..., title="The title of the story")
    chapter_count: int = Field(..., title="The number of chapters in the story")
    user_prompt: str = Field(..., title="The user prompt that generated the story")
    protagonist: Character = Field(..., title="The protagonist of the story")
    characters: List[Character] = Field(..., title="List of characters in the story")
    moral: str = Field(..., title="The moral of the story")
    chapters: List[Chapter] = Field(..., title="List of chapters in the given text")


STRUCTURED_STORY_GENERATOR_SYSTEM_PROMPT = ""

STRUCTURED_STORY_GENERATOR_INSTRUCTIONS = ""


def get_word_count(story_mode: AspectRatio):
    chapter_word_count, scene_count = "450-500", 20
    if story_mode == AspectRatio.PORTRAIT:
        chapter_word_count, scene_count = "450-500", 20
    return chapter_word_count, scene_count


def get_system_prompt(chapter_count: int, story_mode: AspectRatio):
    chapter_word_count, scene_count = get_word_count(story_mode)
    return f"""
You are tasked with generating a structured breakdown of a story based on the user's prompt. The output should be in JSON format, following a specific schema. The story should be divided into multiple chapters, with each chapter containing at least {scene_count} scenes that provide a distinct segment of the narrative. The story should also include detailed character descriptions and other elements such as background music and image prompts for each scene.

Follow the provided schema to organize the content into the following categories:

1. **Story Breakdown**: 
   - Title of the story
   - Number of chapters in the story
   - User prompt that generated the story
   - The protagonist's character description
   - A list of other characters with their descriptions
   - The moral of the story

2. **Chapters**:
   - Each chapter should have a title and a list of scenes.
   - Each chapter should have at least {scene_count} scenes.
   _ Ensure each scene has a maximum of 2 characters.
   - Each scene should contain:
     - **Narration text**: A minimum of 2 and a maximum of 3 sentences or at least 20 words that summarize the scene's content.
     - **Image prompt**: A descriptive prompt for generating an image that fits the scene's mood. The prompt should focus on the 2 characters in the scene. If any more characters are present, they should be mentioned such that they are in the backgound. The protagonist should be in the foreground always. Always include the age, physical description of all the charaters. 
     - **Music prompt**: A description of background music that would accompany the scene.

3. **Character Descriptions**:
   - Provide a name and a brief description of each character.

You will generate {chapter_count} chapters, each containing {chapter_word_count} words in total, with atleast {scene_count} scenes per chapter.

You will output all data in JSON format, following this schema:

{StructuredStoryResponseModel.model_json_schema()}
"""


def get_instructions(chapter_count: int, story_mode: AspectRatio):
    chapter_word_count, scene_count = get_word_count(story_mode)
    return f"""
Introduction: Begin by reading the user's provided prompt. Understand the general theme, setting, characters, and tone of the story.

Protagonist and Characters:

    Identify the protagonist and describe their role in the story, personality traits, appearance, and motivations.
    Identify other significant characters in the story and provide brief descriptions of them as well.

Story Breakdown:

    The title of the story should reflect the central theme or event in the user's prompt.
    The number of chapters should align with the number of chapters requested by the user.
    Include the user's prompt as part of the breakdown.
    Identify the moral lesson the story conveys.

Chapters and Scenes:
    Ensure there are excactly {chapter_count} chapters in the story.
    For each chapter:
        Choose a fitting title based on the events of the chapter.
        Divide the chapter into scenes.
        Ensure that each chapter has at least {scene_count} scenes.
        Each scene should have:
            Narration text: A concise and coherent description of the scene (minimum of 2 sentences, maximum of 3 sentences or at least 20 words).
            Image prompt: A descriptive prompt for generating an image that fits the scene's mood. The prompt should focus on the 2 characters in the scene. If any more characters are present, they should be mentioned such that they are in the backgound. The protagonist should be in the foreground always. Always include the age, physical description of all the charaters.
            Music prompt: A suggestion for background music that complements the scene's tone (e.g., ambient, intense, melancholic).

Formatting:

    Ensure each chapter and scene is described in the appropriate format, with the chapter having a title and a list of scenes.
    Each scene includes a narration, an image prompt, and a music prompt.
    Ensure that the total word count for each chapter remains between {chapter_word_count} words.

Final Output:

    Return the final output in JSON format with all the sections (protagonist, characters, chapters, etc.) properly filled out and aligned with the schema.

Tone:

    Keep the tone consistent with the story's mood (e.g., light, dark, adventurous).
    Ensure that descriptions for music and images reflect the scene's atmosphere and tone.
"""


class StructuredStoryGenerator(BaseAgent):
    def get_agent(
        self,
        chapter_count: int = 3,
        story_mode: AspectRatio = AspectRatio.PORTRAIT,
    ):
        return Agent(
            model=Gemini(id=MODEL_NAME),
            system_prompt=get_system_prompt(chapter_count=chapter_count, story_mode=story_mode),
            instructions=get_instructions(chapter_count=chapter_count, story_mode=story_mode),
            response_model=StructuredStoryResponseModel,
            structured_outputs=True,
        )

    def run(
        self,
        premise: str,
        chapter_count: int,
        audience: str,
        characters: str,
        story_mode: AspectRatio,
        cache: bool = False,
    ) -> StructuredStory:
        query = f"The story is about {premise}. These are the main charaters of the story: {characters}. The story has {chapter_count} chapters and is intended for {audience}."
        print(f"Generating story for query: {query}")

        if cache:
            structured_story = get_random_structured_story()
            if structured_story:
                print(f"Returning cached story: {structured_story}")
                return structured_story

        response = self.get_agent(chapter_count=chapter_count, story_mode=story_mode).run(query)
        structured_story_response: StructuredStoryResponseModel = response.content
        chapter_names = [chapter.title for chapter in structured_story_response.chapters]
        chapters = []
        for chapter in structured_story_response.chapters:
            chapters.append(
                [
                    SceneModel(
                        narration_text=scene.narration_text,
                        image_prompt=scene.image_prompt,
                        music_prompt=scene.music_prompt,
                    )
                    for scene in chapter.scenes
                ]
            )
        structured_story = StructuredStory(
            title=structured_story_response.title,
            chapter_count=structured_story_response.chapter_count,
            user_prompt=structured_story_response.user_prompt,
            protagonist=structured_story_response.protagonist,
            characters=structured_story_response.characters,
            moral=structured_story_response.moral,
            chapter_names=chapter_names,
            chapters=chapters,
        )
        assert chapter_count == structured_story_response.chapter_count
        print(f"Generated story: {structured_story}")
        _ = save_structured_story(structured_story)
        return structured_story


if __name__ == "__main__":
    # print(StructuredStoryResponseModel.model_json_schema())
    StructuredStoryGenerator().run(
        chapter_count=3,
        audience="children",
        premise="friendship",
        characters="7 year old boy and his dog",
        story_mode=AspectRatio.PORTRAIT,
    )

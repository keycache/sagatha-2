from phi.agent import Agent
from phi.model.google import Gemini

from src.agents.agent_constants import SCENE_BREAKDOWN_GENERATOR_INSTRUCTIONS, SCENE_BREAKDOWN_GENERATOR_SYSTEM_PROMPT
from src.agents.agent_utils import get_random_story, get_random_structured_story, save_scene_breakdown
from src.agents.base import BaseAgent
from src.agents.response_models import (
    SceneBreakdownGeneratorResponseModel,
    StoryGeneratorResponseModel,
    StructuredStory,
)
from src.constants import MODEL_NAME


class SceneBreakdownGenerator(BaseAgent):
    @property
    def agent(self):
        return Agent(
            model=Gemini(id=MODEL_NAME),
            system_prompt=SCENE_BREAKDOWN_GENERATOR_SYSTEM_PROMPT,
            instructions=SCENE_BREAKDOWN_GENERATOR_INSTRUCTIONS,
            response_model=SceneBreakdownGeneratorResponseModel,
            structured_outputs=True,
        )

    def run(self, story: StoryGeneratorResponseModel, cache: bool = False) -> StructuredStory:
        if cache:
            structured_story = get_random_structured_story()
            if structured_story:
                print(f"Returning cached structured-story: {structured_story}")
                return structured_story
        structured_story = StructuredStory(**story.model_dump(), scenes=[])
        for i, chapter in enumerate(story.chapters, start=1):
            print(f"Breaking down the scenes for chapter {i}/{len(story.chapters)} of the story: {story.title}")
            for _ in range(3):
                try:
                    out = self.agent.run(chapter)
                    structured_story.scenes.append(out.content.response)
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    print(out.content)
                    print(f"Retrying...")
        save_scene_breakdown(structured_story)
        return structured_story


if __name__ == "__main__":
    story: StoryGeneratorResponseModel = get_random_story(
        r".data\stories\timmy-and-buster-a-tail-of-friendship\1-raw-story-timmy-and-buster-a-tail-of-friendship.json"
    )
    out = SceneBreakdownGenerator().run(story)
    print(out)

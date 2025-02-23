from phi.agent import Agent
from phi.model.google import Gemini

from src.agents.agent_constants import STORY_GENERATOR_INSTRUCTIONS, STORY_GENERATOR_SYSTEM_PROMPT
from src.agents.agent_utils import get_random_story, save_story
from src.agents.base import BaseAgent
from src.agents.response_models import StoryGeneratorResponseModel
from src.constants import MODEL_NAME


class StoryGenerator(BaseAgent):
    @property
    def agent(self):
        return Agent(
            model=Gemini(id=MODEL_NAME),
            system_prompt=STORY_GENERATOR_SYSTEM_PROMPT,
            instructions=STORY_GENERATOR_INSTRUCTIONS,
            response_model=StoryGeneratorResponseModel,
            structured_outputs=True,
        )

    def run(self, query: str, chapter_count: int, audience: str, cache: bool = False) -> StoryGeneratorResponseModel:
        query = f"{query} with {chapter_count} chapters for {audience}"
        print(f"Generating story for query: {query}")
        if cache:
            story = get_random_story()
            if story:
                print(f"Returning cached story: {story}")
                return story
        response = self.agent.run(query)
        content: StoryGeneratorResponseModel = response.content
        assert chapter_count == len(content.chapters)
        print(f"Generated story: {content}")
        save_story(story=content)
        return content


if __name__ == "__main__":
    StoryGenerator().run(
        "Story about little boy and his friendship with his dog",
        chapter_count=3,
        audience="children",
    )

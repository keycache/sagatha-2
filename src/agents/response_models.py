from typing import List, Optional

from pydantic import BaseModel, Field


class Character(BaseModel):
    name: str = Field(..., title="The name of the character")
    description: str = Field(..., title="A physical description of the character")


class StoryGeneratorResponseModel(BaseModel):
    user_prompt: str = Field(..., title="User Prompt used to generate the story")
    title: str = Field(..., title="Title of the story")
    protogonist: Character = Field(..., title="The protagonist of the story")
    characters: List[Character] = Field(..., title="List of characters in the story")
    moral: str = Field(..., title="Moral of the story")


class SceneModel(BaseModel):
    narration_text: str = Field(
        ..., title="Narration text for the scene. This should not be more than 1 or 2 sentences."
    )
    image_prompt: str = Field(
        ...,
        title="A detailed description for a text-to-image model, focusing on visual elements. Should not include any charater names. ",
    )
    music_prompt: str = Field(
        ..., title="A brief description of background music that would match the mood of the scene"
    )


class SceneBreakdownGeneratorResponseModel(BaseModel):
    response: List[SceneModel] = Field(..., title="List of scenes in the given text")


class StructuredStory(BaseModel):
    title: str = Field(..., title="Title of the story")
    chapter_count: int = Field(..., title="Number of chapters in the story")
    chapter_names: List[str] = Field(..., title="List of chapter names in the story")
    user_prompt: str = Field(..., title="User prompt used to generate the story")
    protagonist: Character = Field(..., title="The protagonist of the story")
    characters: List[Character] = Field(..., title="List of characters in the story")
    moral: str = Field(..., title="Moral of the story")
    chapters: List[List[SceneModel]] = Field(
        ...,
        title="List of chapters broken down into scenes. Each chapter should has at least 20 scenes.",
    )


class AssetModel(BaseModel):
    path: str
    seed: int
    prompt: str
    model_name: str


class AssetSceneModel(BaseModel):
    narration: Optional[List[AssetModel]] = None
    image: Optional[List[AssetModel]] = None
    music: Optional[List[AssetModel]] = None


class StructuredStoryAsset(BaseModel):
    title: str
    # chapters: List[str]
    chapter_names: List[str]
    protogonist: Character
    characters: List[Character]
    moral: str
    chapter_scenes: List[List[AssetSceneModel]]
    # chapter_scenes = [
    #     [
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #     ],
    #     [
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #     ],
    #     [
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #         AssetSceneModel(narration=[], image=[], music=[]),
    #     ],

    # ]

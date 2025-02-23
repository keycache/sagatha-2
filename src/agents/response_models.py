from typing import List, Optional

from pydantic import BaseModel, Field


class StoryGeneratorResponseModel(BaseModel):
    user_prompt: str = Field(..., title="User Prompt used to generate the story")
    title: str = Field(..., title="Title of the story")
    chapters: List[str] = Field(
        ...,
        title="List of chapters in the story. Every chapter should be between 300 to 350 words",
    )
    protogonist: str = Field(
        ...,
        title="Name and Description(describing the looks and features) of the main character of the story",
    )
    characters: List[str] = Field(..., title="List of characters in the story")
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
    chapters: List[str] = Field(
        ..., title="List of chapters in the story. Every chapter should be between 300 to 350 words"
    )
    protogonist: str = Field(
        ..., title="Name and Description(describing the looks and features) of the main character of the story"
    )
    characters: List[str] = Field(..., title="List of characters in the story")
    moral: str = Field(..., title="Moral of the story")
    scenes: List[List[SceneModel]] = Field(
        ...,
        title="List of scenes in the story. The list corresponds to the chapters. All the scenes that make up the chapter should have around 300 to 350 words.",
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
    chapters: List[str]
    protogonist: str
    characters: List[str]
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

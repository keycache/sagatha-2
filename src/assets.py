import mimetypes
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# load_dotenv("../.env")


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    files = [
        # Make the file available in local system working directory
        client.files.upload(file=".data/images/reference.jpg"),
    ]
    model = "gemini-2.0-flash-exp-image-generation"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_text(
                    text="""Based on the portrait images. Generate a visual story by creating around 15 to 20 images to visually represent the below story. Along with the picture output the \"as is part of the story\" that could be narrated
Varin was a curious boy. He loved reading books about faraway lands and dreamed of adventures. One afternoon, while exploring his attic, he stumbled upon a dusty old chest. Inside, he found a rolled-up parchment tied with a faded ribbon. As he unfurled it, the parchment shimmered, revealing itself as a map unlike any he had ever seen. It wasn't just paper; it seemed to be alive, with tiny rivers flowing and miniature mountains rising.\\n\\nSuddenly, an old man with a long white beard appeared beside him. \"That, my boy,\" he said with a twinkle in his eye, \"is a Magical Map of Mysteries. It can take you anywhere you wish! I am Professor Zoom. I've been waiting for someone with a thirst for adventure to find it.\" Varin was overjoyed. He asked Professor Zoom how it worked. \"Just point to a place, say the magic words – 'Mundo Vagus!' – and you'll be there!\" Professor Zoom instructed.\\n\\nVarin, eager to start his adventure, decided to visit the Eiffel Tower in Paris. He pointed at the tiny Eiffel Tower on the map and shouted, \"Mundo Vagus!\" The attic swirled around him, and in a flash, he found himself standing in a bustling Parisian square, the real Eiffel Tower looming before him. He saw people eating croissants, artists sketching, and mimes performing. He spent the day exploring, but then a pickpocket stole his map!\\n\\nVarin was distraught. He chased the pickpocket through the crowded streets, yelling for him to stop. The chase led them to a small park, where the pickpocket tripped and dropped the map. Varin quickly snatched it up, relieved. The pickpocket, a young boy not much older than Varin, looked ashamed.\\n\\nVarin, instead of being angry, felt sorry for the boy. He learned that the boy was hungry and stole to buy food. Varin, remembering the croissants he had seen earlier, bought one for the boy and one for himself. They sat together, eating and chatting. Varin realized that even in exciting new places, there were people in need. The pickpocket apologized, promising to find a better way to earn a living. Varin felt good about helping. He said goodbye to the boy and, pointing to his home on the map, shouted, \"Mundo Vagus!\" He was back in his attic, the adventure over, but the lesson learned.
"""
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_modalities=[
            "image",
            "text",
        ],
        response_mime_type="text/plain",
    )

    for i, chunk in enumerate(
        client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
    ):
        if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
            continue
        if chunk.candidates[0].content.parts[0].inline_data:
            file_name = f".data/images/output_{i}"
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", inline_data.data)
            print("File of mime type" f" {inline_data.mime_type} saved" f"to: {file_name}")
        else:
            with open(f".data/text/output_{i}.txt", "w") as f:
                f.write(chunk.text)
            # print(chunk.text)

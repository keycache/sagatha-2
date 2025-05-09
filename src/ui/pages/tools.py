import time

import streamlit as st
from PIL import Image

from src.agent_gemini import generate_image, remove_watermark
from src.constants import AspectRatioDetails
from src.ui.utils import get_settings_ardetails

with st.expander("**Resize & DeWatermark**", expanded=False):
    file_path: str = st.text_input("Enter the path to the image file:")
    if file_path:
        remove_watermark(file_path, file_path)
        ardetails: AspectRatioDetails = get_settings_ardetails()
        image = Image.open(file_path)
        image = image.resize((ardetails.width, ardetails.height))
        image.save(file_path)
        st.toast("Image Resized & DeWatermarked")

with st.expander("**Create Image**", expanded=False):
    image = None
    image_prompt = st.text_area("Image Prompt", placeholder="Write your image prompt here...")
    cover_image_path = st.text_input("Cover Image Path", placeholder="Enter the path to the cover image file...")
    if st.button("Generate Image", type="primary") and image_prompt:
        print(f"Generating image with cover image: -{cover_image_path}-")
        image = generate_image(image_prompt, cover_image_path=cover_image_path)
        filename = f".data/images/generated_image_{int(time.time() * 1000)}.png"
        image.save(filename)
        st.image(image)
    # if st.button("Save Image", type="primary"):
    #     st.toast(f"Image saved as {filename}")

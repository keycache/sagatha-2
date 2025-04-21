from enum import Enum


class ImageStyle(str, Enum):
    STORY_BOOK_CLASSIC = "Cartoonish, digital painting style, reminiscent of children's book illustrations or animated movie stills. It features smooth shading, soft lighting, and exaggerated, yet appealing, character designs. The colors are vibrant and warm, contributing to a friendly and adventurous atmosphere. The textures, particularly on the map and the wooden surface, are rendered with enough detail to be visually interesting without being overly realistic. The overall style suggests a narrative focus, inviting the viewer into a story. "
    WHIMSICAL_WATERCOLOR = "Imagine soft, translucent washes of color blending gently, creating a dreamy and ethereal quality. The lines might be delicate and slightly uneven, adding to the hand-painted feel. Think of classic children's book illustrations with a focus on flowing shapes and subtle textures."
    VIBRANT_VECTOR_ART = "Clean, crisp lines and bold, flat colors define this style. Shapes are often simplified and stylized, creating a graphic and modern aesthetic. Think of the visuals in many contemporary animated shows or educational apps – bright, engaging, and easily scalable."
    FOLK_ART = "Drawing inspiration from traditional folk art styles around the world, this could involve bold patterns, flat perspectives, and decorative elements. The color palettes might be rich and earthy or bright and celebratory, depending on the specific tradition you draw from."
    STORY_BOOK_RETRO = "This style would evoke the look of vintage comic books, with bold outlines, Ben-Day dots or similar texturing for shading, and a slightly grainier or more saturated color palette. Think of classic adventure comics with a nostalgic feel."
    MODERN_MINIMALIST = "A clean and simple aesthetic, focusing on essential shapes and colors. The design is uncluttered, with a limited color palette and a focus on negative space. This style is often used in contemporary graphic design and illustration, emphasizing clarity and elegance."
    HAND_DRAWN = "A style that mimics the look of hand-drawn illustrations, with visible pencil or ink lines and a slightly imperfect quality. This could include sketchy outlines, textured shading, and a more organic feel. The colors might be softer and less saturated, giving a more personal touch to the visuals."
    MODERN_CARTOON = "A contemporary cartoon style that features bold outlines, exaggerated expressions, and vibrant colors. Characters are often stylized with simplified shapes and playful proportions, creating a fun and engaging visual experience. The backgrounds are typically colorful and dynamic, enhancing the overall whimsical feel of the illustrations."
    MODERN_ANIMATION = "A sleek and polished style that combines 3D elements with 2D animation techniques. This style often features smooth lines, vibrant colors, and a sense of depth and movement. Characters are designed with a modern aesthetic, often incorporating elements of realism while maintaining a playful and engaging look."


class StoryPremise(str, Enum):
    pass


COVER_IMAGE_DESCRIPTION = """
Title Placement: The chapter title is centered in the image, occupying a prominent space in the upper-middle area. Use bold, stylized font that matches the tone of the story (e.g., whimsical, mysterious, adventurous).

Visual Style: Artistic collage with slightly exaggerated, expressive visuals. Blend realistic character art with story-themed background elements to create visual intrigue.

Characters (collaged into the center 70% of the image):
- [Character 1 Name]: [Physical description — age, features, height, clothing, key accessory, expression, pose]. Positioned [location relative to center — e.g., "slightly left and forward-facing"].
- [Character 2 Name]: [Same as above]. Positioned [e.g., "right side, looking over shoulder toward center"].
- [Character 3 Name (if applicable)]: [Optional character or silhouette, to hint at future events or relationships].

Background & Collage Elements:
- Include story-relevant symbols, motifs, or foreshadowing elements blended around or behind characters (e.g., maps, glowing objects, shadowy figures, ancient ruins, magical runes).
- Use a background color or pattern that sets the mood (e.g., twilight sky, foggy forest, sunburst over mountains).
- Subtle environmental layering (e.g., clouds, leaves, sparkles, shadows) to give a dreamy collage feel.

Mood & Intrigue:
- The image should hint at the tone of the chapter (e.g., mystery, adventure, discovery, conflict).
- Expressions and poses should spark curiosity — looking at something unseen, reaching for something, hiding something, or reacting to off-screen action.

Framing:
- Ensure the characters and title are well balanced within the center 70% of the image.
- Edges may include visual effects or overlays (e.g., torn paper edges, ink splashes, vignette) to enhance the collage style.

View: Front-facing or slightly tilted top-down view, with characters arranged in layered depth — one character closer, others behind or beside, to add dimensionality.

Consistency Note: All characters must retain their established appearance, outfits, and proportions from earlier illustrations.
"""

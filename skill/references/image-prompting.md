# Image Prompting Guide

Gemini image model understands intent, physics, composition. Prompt naturally.

## Core Rules

### 1. Natural Language, Not Tags

Write full sentences describing the scene.

Bad: "cool car, neon, city, night, 8k, ultra realistic"
Good: "A cinematic wide shot of a futuristic sports car speeding through a rainy Tokyo street at night. Neon signs reflect off wet pavement and metallic chassis."

### 2. Be Specific

| Element | Vague | Specific |
|---------|-------|----------|
| Subject | "a woman" | "sophisticated elderly woman in vintage Chanel-style suit" |
| Material | "shiny" | "brushed steel with matte finish" |
| Color | "dark green" | "#0d3d2d deep emerald" |
| Position | "on the right" | "right third, bleeding off edge" |
| Lighting | "good lighting" | "golden hour backlight, rim lighting on hair" |

### 3. Provide Context

Context shapes the model's decisions:
- "for a Brazilian gourmet cookbook" -> professional plating, shallow DOF
- "for an executive strategy presentation" -> corporate aesthetic, clean
- "for a children's educational app" -> friendly, colorful, rounded shapes

### 4. Quote Text Exactly

Text to render goes in quotes with styling:
- `"Revenue Growth"` in bold, white, upper third
- `"Start Free Trial"` in extra bold, #3b82f6, centered

### 5. Edit, Don't Re-roll

Image 80% correct? Edit it via `gemini_generate_image` with the `files` parameter:
- "Change the lighting to sunset"
- "Make the text neon blue"
- "Remove the person on the left, fill with background"

```
gemini_generate_image(prompt="Change the sky to dramatic sunset colors. Keep everything else exactly the same.", files=["/path/to/image.png"])
```

## Prompt Template

```
Create a [TYPE] for [CONTEXT].

Background: [Description with hex colors]. [Atmospheric effects].

[HERO ELEMENT]:
[Detailed description — position, lighting, angle, materials]

Typography:
Line 1: "[TEXT]" in [weight], [color], [size], [position]
Line 2: "[TEXT]" in [weight], [color], [size], [position]

[ADDITIONAL ELEMENTS]

Mood: [Emotional descriptor]
Format: [ASPECT RATIO]
```

## Aspect Ratios

Include aspect ratio naturally in prompt. Do NOT specify model — the server picks the best image model automatically.

| Ratio | Use | Prompt hint |
|-------|-----|-------------|
| 1:1 | Social media, avatars | (default, no hint needed) |
| 16:9 | Presentations, headers, thumbnails | "wide landscape 16:9" |
| 9:16 | Stories, vertical banners | "tall portrait 9:16" |
| 4:3 | Blog images, cards | "4:3 format" |

## Style Vocabulary

**Photography:**
- Cinematic, editorial, documentary, street photography
- Shallow DOF, bokeh, tilt-shift
- Golden hour, blue hour, overcast, dramatic single source

**Art styles:**
- Oil painting, watercolor, gouache, ink wash
- Digital art, concept art, matte painting
- Isometric 3D, low poly, voxel art

**Materials:**
- Brushed steel, polished chrome, matte ceramic
- Frosted glass, iridescent acrylic, velvet
- Weathered wood, aged leather, raw concrete

**Atmosphere:**
- Volumetric fog, lens flare, light rays
- Rain reflections, dust particles, steam
- Neon glow, bioluminescence, aurora

## Reference Images

Upload images via `gemini_generate_image` with the `files` parameter for editing.

**Match existing style:**
```
[Upload image]
Create content following this exact layout and style.
Replace [ELEMENT] with [NEW CONTENT].
Keep colors, typography, composition.
```

**Keep face, change scene:**
```
[Upload portrait]
Use this person's face. Keep features exactly the same.
Change: [expression/pose/setting]
```

**Product in new context:**
```
[Upload product photo]
Place this product in [NEW CONTEXT].
Match lighting and perspective.
```

**Combine multiple references:**
Upload each image separately, reference by order:
```
[Upload face, then outfit reference, then background]
Face from first image, outfit style from second, setting from third.
```

## Complex Scenes: JSON Structure

For scenes with 5+ detailed elements, use JSON in prompt:

```json
{
  "subject": {
    "description": "main subject",
    "expression": "emotion/pose",
    "clothing": {"top": "...", "bottom": "..."}
  },
  "photography": {
    "angle": "eye-level",
    "shot_type": "waist-up",
    "aspect_ratio": "16:9"
  },
  "background": {
    "setting": "location",
    "lighting": "soft natural",
    "atmosphere": "volumetric fog"
  }
}
```

## Anti-Patterns

- Tag soup: "cool, modern, 4k, ultra HD, masterpiece"
- External refs: "like Apple design" or "in style of [artist]"
- Vague colors: "dark green" -> use hex #228b22
- Re-rolling when 80% correct -> edit via upload instead
- Expecting 4K: native resolution is 1024-1376px, 2x upscale to ~2800px
- Specifying model explicitly: let the server pick the best image model

---
name: gemini-mcp
description: Use Google Gemini for image generation, text chat, file analysis, URL/YouTube analysis, and multi-turn conversations via MCP. Triggers on requests to generate images with Gemini, chat with Gemini, analyze files/URLs/videos with Gemini, use Gemini models, or when user asks to create/edit images and needs prompting guidance. Do NOT use for DALL-E, Midjourney, Stable Diffusion, or OpenAI image generation.
---

# Gemini MCP Skill

Interact with Google Gemini via `gemini-webapi-mcp` MCP server.

## Reference Router

| Task | Read |
|------|------|
| Tool parameters, models, troubleshooting | [tools.md](references/tools.md) |
| Image generation prompting | [image-prompting.md](references/image-prompting.md) |

## Quick Start

**Chat:**
```
gemini_chat(prompt="Explain quantum computing")
```

**Generate image:**
```
gemini_generate_image(prompt="A cinematic wide shot of a futuristic city at sunset, volumetric fog, neon reflections on wet streets")
```

**Edit image:**
```
gemini_generate_image(prompt="Change the background to a sunset beach. Keep everything else exactly the same.", files=["/path/to/image.png"])
```

**Analyze file:**
```
gemini_upload_file(file_path="/path/to/doc.pdf", prompt="Summarize key points")
```

**Analyze URL/YouTube:**
```
gemini_analyze_url(url="https://youtube.com/watch?v=...", prompt="Summarize this video")
```

## Key Facts

- Images saved to `~/Pictures/gemini/` as PNG, 2x upscaled resolution
- Watermark auto-removed (built-in, no extra dependencies)
- Include "16:9" or "9:16" in prompt for non-square aspect ratios
- Do NOT specify model for image generation — server picks the best one automatically
- Auth errors: call `gemini_reset` to refresh cookies
- Models and full parameter reference: see [tools.md](references/tools.md)

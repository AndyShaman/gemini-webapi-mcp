---
name: gemini-mcp
description: Use Google Gemini for image generation, text chat, file analysis, URL/YouTube analysis, and multi-turn conversations via MCP. Triggers on requests to generate images with Gemini, chat with Gemini, analyze files/URLs/videos with Gemini, use Gemini models, or when user asks to create/edit images and needs prompting guidance.
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
mcp-cli call gemini gemini_chat '{"prompt": "Explain quantum computing"}'
```

**Generate image:**
```
mcp-cli call gemini gemini_generate_image '{"prompt": "A cinematic wide shot of a futuristic city at sunset, volumetric fog, neon reflections on wet streets"}'
```

**Edit image:**
```
mcp-cli call gemini gemini_generate_image '{"prompt": "Change the background to a sunset beach. Keep everything else exactly the same.", "files": ["/path/to/image.png"]}'
```

**Analyze file:**
```
mcp-cli call gemini gemini_upload_file '{"file_path": "/path/to/doc.pdf", "prompt": "Summarize key points"}'
```

**Analyze URL/YouTube:**
```
mcp-cli call gemini gemini_analyze_url '{"url": "https://youtube.com/watch?v=...", "prompt": "Summarize this video"}'
```

## Models

| Model | Default for | Notes |
|-------|-------------|-------|
| `gemini-3.0-flash` | chat, analysis | Fast |
| `gemini-3.0-pro` | image generation | Supports aspect ratios |
| `gemini-3.0-flash-thinking` | — | Complex reasoning, shows thought process |

## Key Facts

- Images saved to `~/Pictures/gemini/` as PNG, native resolution 1024-1376px
- Watermark auto-removed if `onnxruntime` installed
- Only Pro supports non-square aspect ratios (include "16:9" etc. in prompt)
- Auth errors: call `gemini_reset` to refresh cookies
- All tools called via `mcp-cli call gemini <tool> '<json>'`

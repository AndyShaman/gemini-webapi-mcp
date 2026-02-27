# MCP Tools Reference

## gemini_chat

Text prompt to Gemini. Supports multi-turn and thinking mode.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `prompt` | yes | — | Text prompt |
| `model` | no | `gemini-3.0-flash` | Model to use |
| `session_id` | no | — | Session ID for multi-turn |

```
gemini_chat(prompt="Explain quantum computing")
```

Multi-turn:
```
gemini_chat(prompt="Now simpler", session_id="abc123")
```

Thinking mode (shows reasoning):
```
gemini_chat(prompt="Solve step by step: ...", model="gemini-3.0-flash-thinking")
```

## gemini_start_chat

Start multi-turn session. Returns `session_id` for use in `gemini_chat`.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `model` | no | `gemini-3.0-flash` | Model for session |

```
gemini_start_chat()
gemini_start_chat(model="gemini-3.0-pro")
```

## gemini_generate_image

Generate new images or edit existing ones. Watermark auto-removed if `onnxruntime` installed.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `prompt` | yes | — | Image description or editing instruction |
| `files` | no | — | List of file paths for image editing |
| `model` | no | `gemini-3.0-flash-thinking` | Image model (Nano Banana 2, supports aspect ratios) |

**Generate:**
```
gemini_generate_image(prompt="a serene mountain lake at sunset, oil painting style")
```

**Edit existing image:**
```
gemini_generate_image(prompt="make the sky purple", files=["/path/to/image.png"])
```

**Output:** PNG saved to `~/Pictures/gemini/`, 2x upscaled resolution. Watermark auto-removed.

**Resolution (2x upscale):**
- 16:9: 2816x1536 (native 1408x768, auto-upscaled 2x)
- 9:16: 1536x2816 (native 768x1408, auto-upscaled 2x)
- 1:1: 2048x2048 (native 1024x1024, auto-upscaled 2x)
- Fallback to native if 2x unavailable

**Aspect ratio:** Include in prompt naturally: "wide landscape 16:9", "tall portrait 9:16". Do NOT specify model explicitly — the server picks the best image model automatically.

## gemini_upload_file

Upload file and ask Gemini about it. Supports video, images, PDF, documents.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `file_path` | yes | — | Absolute path to file |
| `prompt` | no | `"Describe this file."` | Question or instruction |
| `model` | no | `gemini-3.0-flash` | Model to use |

```
gemini_upload_file(file_path="/path/to/image.png", prompt="What is in this image?")
```

> For **image editing**, use `gemini_generate_image` with the `files` parameter instead.

## gemini_analyze_url

Analyze URL — YouTube videos, webpages, articles.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `url` | yes | — | URL to analyze |
| `prompt` | no | `"Summarize this content."` | Question about the content |
| `model` | no | `gemini-3.0-flash` | Model to use |

```
gemini_analyze_url(url="https://youtube.com/watch?v=...", prompt="Summarize this video")
```

## gemini_reset

Re-initialize client when cookies expire. No parameters.

```
gemini_reset()
```

**When to use:** Auth errors, 401/403 responses, "cookie expired" messages.

## Models

| Model | Best for | Notes |
|-------|----------|-------|
| `gemini-3.0-flash` | Text chat, analysis | Fast, default for chat |
| `gemini-3.0-flash-thinking` | Image generation, editing | Nano Banana 2, supports aspect ratios, default for images |
| `gemini-3.0-pro` | Complex reasoning | Slower, higher quality text |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Auth error / cookies expired | `gemini_reset` |
| Stream interrupted / timeout | Server auto-retries; for heavy prompts with files, wait up to 5 min |
| No images in response | Prompt may violate content policy, rephrase |
| Square image despite aspect ratio | Include "16:9" or "9:16" in prompt text |

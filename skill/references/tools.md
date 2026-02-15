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
mcp-cli call gemini gemini_chat '{"prompt": "Explain quantum computing"}'
```

Multi-turn:
```
mcp-cli call gemini gemini_chat '{"prompt": "Now simpler", "session_id": "abc123"}'
```

Thinking mode (shows reasoning):
```
mcp-cli call gemini gemini_chat '{"prompt": "Solve step by step: ...", "model": "gemini-3.0-flash-thinking"}'
```

## gemini_start_chat

Start multi-turn session. Returns `session_id` for use in `gemini_chat`.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `model` | no | `gemini-3.0-flash` | Model for session |

```
mcp-cli call gemini gemini_start_chat '{}'
mcp-cli call gemini gemini_start_chat '{"model": "gemini-3.0-pro"}'
```

## gemini_generate_image

Generate new images or edit existing ones. Watermark auto-removed if `onnxruntime` installed.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `prompt` | yes | — | Image description or editing instruction |
| `files` | no | — | List of file paths for image editing |
| `model` | no | `gemini-3.0-pro` | Model (Pro supports aspect ratios) |

**Generate:**
```
mcp-cli call gemini gemini_generate_image '{"prompt": "a serene mountain lake at sunset, oil painting style"}'
```

**Edit existing image:**
```
mcp-cli call gemini gemini_generate_image '{"prompt": "make the sky purple", "files": ["/path/to/image.png"]}'
```

**Output:** PNG saved to `~/Pictures/gemini/`, full native resolution.

**Resolution:**
- Flash: always 1024x1024
- Pro: supports aspect ratios (e.g. 1376x768 for 16:9)
- Native resolution 1024-1376px, no upscaling

**Aspect ratio:** Include in prompt naturally: "wide landscape 16:9", "tall portrait 9:16". Only Pro respects this — Flash always square.

## gemini_upload_file

Upload file and ask Gemini about it. Supports video, images, PDF, documents.

**Parameters:**
| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `file_path` | yes | — | Absolute path to file |
| `prompt` | no | `"Describe this file."` | Question or instruction |
| `model` | no | `gemini-3.0-flash` | Model to use |

```
mcp-cli call gemini gemini_upload_file '{"file_path": "/path/to/image.png", "prompt": "What is in this image?"}'
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
mcp-cli call gemini gemini_analyze_url '{"url": "https://youtube.com/watch?v=...", "prompt": "Summarize this video"}'
```

## gemini_reset

Re-initialize client when cookies expire. No parameters.

```
mcp-cli call gemini gemini_reset '{}'
```

**When to use:** Auth errors, 401/403 responses, "cookie expired" messages.

## Models

| Model | Best for | Notes |
|-------|----------|-------|
| `gemini-3.0-flash` | Text chat, analysis | Fast, default for chat |
| `gemini-3.0-pro` | Image generation, editing | Supports aspect ratios, default for images |
| `gemini-3.0-flash-thinking` | Complex reasoning | Shows thought process |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Auth error / cookies expired | `gemini_reset` |
| Image generation error 1052 | Model IDs rotated by Google, need update in server.py `_MODEL_ID_MAP` |
| No images in response | Prompt may violate content policy, rephrase |
| Square image despite aspect ratio | Using Flash instead of Pro, or aspect ratio not in prompt |

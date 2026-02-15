"""
MCP Server for Google Gemini via browser cookies.

Uses gemini_webapi library to access Gemini Web App for free,
without requiring paid API keys. Authentication is done through
browser cookies (__Secure-1PSID and __Secure-1PSIDTS).
"""

import asyncio
import json
import logging
import os
import re
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context

# ---------------------------------------------------------------------------
# Logging (stderr only — stdout reserved for MCP stdio transport)
# ---------------------------------------------------------------------------
logger = logging.getLogger("gemini_mcp")
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IMAGES_DIR = Path.home() / "Pictures" / "gemini"
DEFAULT_MODEL = "gemini-3.0-flash"

# Browser-compatible request parameters for proper image generation.
# Without these, the API returns 1024x1024 images regardless of prompt.
# With these, the API returns images with correct aspect ratios and
# gg-dl URLs that support full-resolution downloads.
_BROWSER_PARAMS = {
    1: ["en"],
    6: [1],
    10: 1,
    11: 0,
    17: [[2]],
    18: 0,
    27: 1,
    30: [4],
    41: [1],
    53: 0,
    68: 2,
}

# Library's model IDs are outdated. Map old → current browser values.
_MODEL_ID_MAP = {
    "fbb127bbb056c959": "56fdd199312815e2",   # Flash
    "9d8ca3786ebdfbea": "e6fa609c3fa255c0",   # Pro
    "5bf011840784117a": "e051ce1aa80aa576",   # Flash-Thinking
}

# ---------------------------------------------------------------------------
# Cookie resolution: env vars → browser-cookie3 → error
# ---------------------------------------------------------------------------

def _resolve_cookies() -> tuple[str, str]:
    """Resolve Gemini auth cookies with clear priority chain.

    1. Environment variables GEMINI_PSID / GEMINI_PSIDTS (explicit override).
    2. Chrome browser cookies via browser-cookie3 (automatic).
    3. RuntimeError with actionable instructions.

    Returns (psid, psidts). psidts may be empty.
    Cookie values are never logged.
    """
    # --- Priority 1: explicit env vars ---
    psid = os.environ.get("GEMINI_PSID", "")
    psidts = os.environ.get("GEMINI_PSIDTS", "")
    if psid:
        logger.info("Using Gemini cookies from environment variables")
        return psid, psidts

    # --- Priority 2: Chrome browser cookies ---
    try:
        import browser_cookie3

        cj = browser_cookie3.chrome(domain_name=".google.com")
        for cookie in cj:
            if cookie.name == "__Secure-1PSID" and cookie.value:
                psid = cookie.value
            elif cookie.name == "__Secure-1PSIDTS" and cookie.value:
                psidts = cookie.value
        if psid:
            logger.info("Using Gemini cookies from Chrome browser")
            return psid, psidts
        logger.warning("browser-cookie3: no __Secure-1PSID cookie found in Chrome")
    except ImportError:
        logger.warning("browser-cookie3 not installed — cannot read cookies from Chrome")
    except Exception as exc:
        logger.warning("browser-cookie3: failed to read Chrome cookies — %s", type(exc).__name__)

    # --- Nothing worked ---
    raise RuntimeError(
        "Gemini cookies not found. Options:\n"
        "  1. Log into gemini.google.com in Chrome and install browser-cookie3, or\n"
        "  2. Set GEMINI_PSID (and optionally GEMINI_PSIDTS) environment variables."
    )


# ---------------------------------------------------------------------------
# Lifespan: initialise GeminiClient once, reuse across all tool calls
# ---------------------------------------------------------------------------

@asynccontextmanager
async def app_lifespan(server):
    from gemini_webapi import GeminiClient

    psid, psidts = _resolve_cookies()

    client = GeminiClient(secure_1psid=psid, secure_1psidts=psidts or None)
    await client.init(timeout=120, auto_close=False, auto_refresh=True)
    _patch_client(client)

    yield {"gemini_client": client, "chat_sessions": {}}

    await client.close()


mcp = FastMCP("gemini-webapi-mcp", lifespan=app_lifespan)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client(ctx: Context):
    return ctx.request_context.lifespan_context["gemini_client"]


def _get_sessions(ctx: Context) -> dict:
    return ctx.request_context.lifespan_context["chat_sessions"]


_image_mode = False
_image_lock = asyncio.Lock()


def _patch_client(gemini_client):
    """Patch GeminiClient to send browser-compatible requests.

    Intercepts StreamGenerate requests to:
    1. Inject browser payload parameters for image generation (only when _image_mode is set).
    2. Update outdated model IDs in the x-goog-ext header.
    3. Add extra browser headers (x-goog-ext-73010989, x-goog-ext-525005358).
    """
    http = gemini_client.client  # httpx.AsyncClient
    _orig_stream = http.stream

    def patched_stream(method, url, **kwargs):
        global _image_mode
        if method == "POST" and "StreamGenerate" in str(url):
            headers = kwargs.get("headers") or {}

            # --- Always patch model header: update outdated IDs ---
            model_hdr = headers.get("x-goog-ext-525001261-jspb", "")
            if model_hdr:
                for old_id, new_id in _MODEL_ID_MAP.items():
                    if old_id in model_hdr:
                        model_hdr = model_hdr.replace(old_id, new_id)
                        break
                headers["x-goog-ext-525001261-jspb"] = model_hdr

            # --- Image mode only: body params, trailing value, extra headers ---
            if _image_mode:
                data = kwargs.get("data")
                if data and "f.req" in data:
                    try:
                        outer = json.loads(data["f.req"])
                        inner = json.loads(outer[1])
                        while len(inner) < 69:
                            inner.append(None)
                        for idx, val in _BROWSER_PARAMS.items():
                            inner[idx] = val
                        outer[1] = json.dumps(inner)
                        data["f.req"] = json.dumps(outer)
                        kwargs["data"] = data
                    except (json.JSONDecodeError, IndexError, TypeError):
                        pass

                if model_hdr:
                    model_hdr = re.sub(r",1\]$", ",2]", model_hdr)
                    headers["x-goog-ext-525001261-jspb"] = model_hdr

                headers["x-goog-ext-73010989-jspb"] = "[0]"
                headers["x-goog-ext-525005358-jspb"] = json.dumps(
                    [str(uuid.uuid4()), 1]
                )

            kwargs["headers"] = headers

        return _orig_stream(method, url, **kwargs)

    http.stream = patched_stream
    logger.info("Patched GeminiClient with browser-compatible parameters")


def _handle_error(e: Exception) -> str:
    from gemini_webapi import AuthError, APIError, TimeoutError as GeminiTimeout

    if isinstance(e, AuthError):
        return (
            "Error: Authentication failed. Cookies may have expired. "
            "Re-login to gemini.google.com in Chrome, then call gemini_reset."
        )
    if isinstance(e, GeminiTimeout):
        return "Error: Request timed out. Try again or use a lighter model."
    if isinstance(e, APIError):
        return f"Error: Gemini API error — {e}"
    return f"Error: {type(e).__name__} — {e}"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="gemini_start_chat",
    annotations={
        "title": "Start Gemini Chat Session",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def gemini_start_chat(
    ctx: Context,
    model: Optional[str] = None,
) -> str:
    """Start a new multi-turn chat session with Gemini.

    The session maintains conversation history so follow-up messages
    have full context. Pass the returned session_id to gemini_chat.

    Args:
        model: Model name for this session. Defaults to gemini-3.0-flash.

    Returns:
        JSON with session_id to use in subsequent gemini_chat calls.
    """
    try:
        client = _get_client(ctx)
        chat = client.start_chat(model=model or DEFAULT_MODEL)
        session_id = str(uuid.uuid4())[:8]
        _get_sessions(ctx)[session_id] = chat
        return json.dumps({
            "session_id": session_id,
            "model": model or DEFAULT_MODEL,
            "message": f"Chat session started. Use session_id '{session_id}' in gemini_chat.",
        })
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gemini_chat",
    annotations={
        "title": "Gemini Chat",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gemini_chat(
    prompt: str,
    ctx: Context,
    model: Optional[str] = None,
    session_id: Optional[str] = None,
) -> str:
    """Send a text prompt to Google Gemini and get a response.

    Args:
        prompt: The text prompt to send to Gemini.
        model: Model name (e.g. 'gemini-3.0-flash', 'gemini-3.0-pro',
               'gemini-3.0-flash-thinking'). Defaults to gemini-3.0-flash.
        session_id: Optional session ID from gemini_start_chat for
                    multi-turn conversation with context.

    Returns:
        Gemini's text response. When using flash-thinking model,
        also includes the model's reasoning process.
    """
    try:
        client = _get_client(ctx)

        if session_id:
            sessions = _get_sessions(ctx)
            chat = sessions.get(session_id)
            if not chat:
                return f"Error: Session '{session_id}' not found. Start a new one with gemini_start_chat."
            response = await chat.send_message(prompt)
        else:
            response = await client.generate_content(
                prompt, model=model or DEFAULT_MODEL
            )

        text = response.text or "(empty response)"
        thoughts = response.thoughts
        if thoughts:
            return f"**Thinking:**\n{thoughts}\n\n**Response:**\n{text}"
        return text
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gemini_generate_image",
    annotations={
        "title": "Gemini Image Generation",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gemini_generate_image(
    prompt: str,
    ctx: Context,
    model: Optional[str] = None,
    files: Optional[list[str]] = None,
) -> str:
    """Generate or edit images with Gemini.

    Without files: generates a new image from the text prompt.
    With files: edits/transforms the provided image(s) based on the prompt.

    Images are saved to ~/Pictures/gemini/ and full file paths are returned.

    Args:
        prompt: Description of the image to generate, or editing instruction
                (e.g. 'change the background to blue', 'make it a cartoon').
        model: Model name. Defaults to gemini-3.0-pro (supports non-square
               aspect ratios). Flash only generates 1024x1024.
        files: Optional list of file paths to images to edit/transform.

    Returns:
        JSON with generated image paths and metadata, or an error message.
    """
    global _image_mode
    try:
        client = _get_client(ctx)

        # Validate input files
        resolved_files = []
        if files:
            for f in files:
                p = Path(f).expanduser().resolve()
                if not p.exists():
                    return f"Error: File not found — {p}"
                resolved_files.append(str(p))

        async with _image_lock:
            _image_mode = True
            try:
                kwargs = {"model": model or "gemini-3.0-pro"}
                if resolved_files:
                    kwargs["files"] = resolved_files
                response = await client.generate_content(prompt, **kwargs)
            finally:
                _image_mode = False

        if not response.images:
            return response.text or "No images were generated. Try rephrasing your prompt."

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        saved = []

        for i, image in enumerate(response.images):
            # Strip any URL suffix and use =s0 for full-resolution download.
            image.url = re.sub(r"=[^/]*$", "", image.url)
            image.url += "=s0"
            filepath = await image.save(
                path=str(IMAGES_DIR), verbose=False, full_size=False,
            )
            title = getattr(image, "title", None) or f"image_{i}"
            saved.append({"title": title, "path": filepath, "dir": str(IMAGES_DIR)})

        result = {
            "text": response.text or "",
            "images_saved_to": str(IMAGES_DIR),
            "images": saved,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gemini_upload_file",
    annotations={
        "title": "Gemini File Upload & Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gemini_upload_file(
    file_path: str,
    ctx: Context,
    prompt: str = "Describe this file.",
    model: Optional[str] = None,
) -> str:
    """Upload a file (image, PDF, document, video) to Gemini and ask a question about it.

    Args:
        file_path: Absolute path to the file to upload.
        prompt: Question or instruction about the file
                (e.g. 'What is shown in this image?').
        model: Model name. Defaults to gemini-3.0-flash.

    Returns:
        Gemini's text response about the uploaded file.
    """
    try:
        p = Path(file_path).expanduser().resolve()
        if not p.exists():
            return f"Error: File not found — {p}"

        client = _get_client(ctx)
        response = await client.generate_content(
            prompt, model=model or DEFAULT_MODEL, files=[str(p)]
        )
        return response.text or "(empty response)"

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gemini_reset",
    annotations={
        "title": "Reset Gemini Client",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def gemini_reset(ctx: Context) -> str:
    """Re-initialise the Gemini client (refresh cookies, clear state).

    Use this when you get authentication errors or want a fresh session.

    Returns:
        Confirmation message or error.
    """
    try:
        from gemini_webapi import GeminiClient

        old = _get_client(ctx)
        await old.close()

        psid, psidts = _resolve_cookies()

        new_client = GeminiClient(
            secure_1psid=psid, secure_1psidts=psidts or None
        )
        await new_client.init(timeout=30, auto_close=False, auto_refresh=True)
        _patch_client(new_client)

        ctx.request_context.lifespan_context["gemini_client"] = new_client
        return "Gemini client re-initialised with fresh cookies."

    except Exception as e:
        return _handle_error(e)

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
import random
import re
import string
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
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

# ---------------------------------------------------------------------------
# Watermark removal — Reverse Alpha Blending
# Algorithm: original = (watermarked - alpha * 255) / (1 - alpha)
# Credit: AllenK (github.com/allenk/GeminiWatermarkTool, MIT License)
#         GargantuaX (github.com/GargantuaX/gemini-watermark-remover, MIT License)
# ---------------------------------------------------------------------------
_ALPHA_NOISE_FLOOR = 3.0 / 255.0   # ignore quantization noise in alpha map
_ALPHA_THRESHOLD = 0.002            # skip near-zero alpha pixels
_MAX_ALPHA = 0.99                   # avoid division by near-zero
_alpha_maps: dict[int, "np.ndarray"] = {}


def _load_alpha_map(size: int) -> "np.ndarray":
    """Load and cache pre-captured alpha map for given watermark size."""
    if size in _alpha_maps:
        return _alpha_maps[size]

    import numpy as np
    from importlib.resources import files as pkg_files
    from PIL import Image

    base_size = size if size in (48, 96) else 96
    asset_path = pkg_files("gemini_webapi_mcp.assets").joinpath(f"bg_{base_size}.png")
    bg = Image.open(asset_path).convert("RGB")

    if base_size != size:
        bg = bg.resize((size, size), Image.BILINEAR)

    bg_arr = np.array(bg, dtype=np.float32)
    alpha_map = np.max(bg_arr, axis=2) / 255.0
    _alpha_maps[size] = alpha_map
    return alpha_map


def _remove_watermark(image_path: str) -> bool:
    """Remove Gemini sparkle watermark using Reverse Alpha Blending.

    Detects watermark size and position from image dimensions:
    - Both sides > 1024: 96px logo, 64px margins
    - Otherwise: 48px logo, 32px margins

    Returns True if watermark was removed.
    """
    import numpy as np
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    if w < 200 or h < 200:
        return False

    if w > 1024 and h > 1024:
        logo_size, margin_right, margin_bottom = 96, 64, 64
    else:
        logo_size, margin_right, margin_bottom = 48, 32, 32

    wm_x = w - margin_right - logo_size
    wm_y = h - margin_bottom - logo_size

    if wm_x < 0 or wm_y < 0:
        return False

    alpha_map = _load_alpha_map(logo_size)
    pixels = np.array(img, dtype=np.float64)

    for row in range(logo_size):
        for col in range(logo_size):
            raw_alpha = alpha_map[row, col]
            if max(0.0, raw_alpha - _ALPHA_NOISE_FLOOR) < _ALPHA_THRESHOLD:
                continue

            alpha = min(raw_alpha, _MAX_ALPHA)
            inv = 1.0 / (1.0 - alpha)

            py = wm_y + row
            px = wm_x + col
            for c in range(3):
                pixels[py, px, c] = max(0.0, min(255.0, (pixels[py, px, c] - alpha * 255.0) * inv))

    Image.fromarray(pixels.astype(np.uint8)).save(image_path)
    return True


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

        cookie_file = os.environ.get("CHROME_COOKIE_FILE") or None
        cj = browser_cookie3.chrome(domain_name=".google.com", cookie_file=cookie_file)
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


def _make_gen_id() -> str:
    """Generate a client-side gen_id for c8o8Fe RPC (16-char repeating pattern)."""
    base = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return (base * 3)[:16]


# ---------------------------------------------------------------------------
# Lifespan: initialise GeminiClient once, reuse across all tool calls
# ---------------------------------------------------------------------------

@asynccontextmanager
async def app_lifespan(server):
    from gemini_webapi import GeminiClient

    psid, psidts = _resolve_cookies()

    account_index = int(os.environ.get("GEMINI_ACCOUNT_INDEX", "0"))
    client = GeminiClient(secure_1psid=psid, secure_1psidts=psidts or None, account_index=account_index)
    if account_index:
        logger.info("Using Google account index: %d", account_index)
    await client.init(timeout=300, watchdog_timeout=45, auto_close=False, auto_refresh=True)
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

# Populated by _patched_parse hook during StreamGenerate response parsing.
_image_tokens: dict[str, str] = {}   # preview_url -> download_token
_last_metadata: list = []             # [cid, rid, rcid, ...] from last response


def _patch_client(gemini_client):
    """Patch GeminiClient for image generation and 2x download support.

    1. Override model ID in header (Google rotates IDs periodically).
    2. Add browser-compatible body params and extra headers during image generation.
    3. Intercept response parsing to capture image download tokens for c8o8Fe RPC.
    """
    # Google rotates model IDs periodically. Update these when generation fails (error 1052).
    _MODEL_ID_MAP = {
        "5bf011840784117a": "e051ce1aa80aa576",  # flash-thinking (Nano Banana 2)
        "9d8ca3786ebdfbea": "e051ce1aa80aa576",  # pro -> same current ID
        "fbb127bbb056c959": "e051ce1aa80aa576",  # flash -> same current ID
    }

    # Browser-compatible body params (indices in inner_req_list).
    # Without these, certain operations (image editing with files) may fail.
    # Synced with HanaokaYuzu/Gemini-API v1.21.0 (2026-03-06).
    _BROWSER_PARAMS = {
        1: [os.environ.get("GEMINI_LANGUAGE", "en")],
        6: [0],
        10: 1,
        11: 0,
        17: [[0]],
        18: 0,
        27: 1,
        30: [4],
        41: [1],
        53: 0,
        61: [],
        68: 1,
    }

    http = gemini_client.client  # curl_cffi.AsyncSession
    _orig_request = http.request

    async def patched_request(method, url, **kwargs):
        global _image_mode
        if method == "POST" and "StreamGenerate" in str(url) and _image_mode:
            headers = kwargs.get("headers") or {}

            # Remap model ID in the model header
            model_hdr = headers.get("x-goog-ext-525001261-jspb", "")
            if model_hdr:
                for old_id, new_id in _MODEL_ID_MAP.items():
                    if old_id in model_hdr:
                        model_hdr = model_hdr.replace(old_id, new_id)
                        break
                # Update trailing version flag: ,1] -> ,2]
                if model_hdr.endswith(",1]"):
                    model_hdr = model_hdr[:-2] + "2]"
                headers["x-goog-ext-525001261-jspb"] = model_hdr

            headers["x-goog-ext-73010989-jspb"] = "[0]"
            headers["x-goog-ext-73010990-jspb"] = "[0]"
            # Per-request UUID must match between header and body[59]
            req_uuid = str(uuid.uuid4())
            headers["x-goog-ext-525005358-jspb"] = json.dumps(
                [req_uuid, 1]
            )

            kwargs["headers"] = headers

            # Inject browser-compatible body params into f.req
            data = kwargs.get("data")
            if isinstance(data, dict) and "f.req" in data:
                try:
                    outer = json.loads(data["f.req"])
                    inner = json.loads(outer[1])
                    for idx, val in _BROWSER_PARAMS.items():
                        if inner[idx] is None:
                            inner[idx] = val
                    # Sync UUID with header (upstream HanaokaYuzu v1.21)
                    inner[59] = req_uuid

                    # Fix file_data format:
                    # Library:  [[[url], "name"]]
                    # Browser:  [[[url, 1, null, "mime"], "name", null*6, [0]]]
                    file_data = inner[0][3] if isinstance(inner[0], list) and len(inner[0]) > 3 else None
                    if file_data and isinstance(file_data, list):
                        _MIME_MAP = {
                            ".png": "image/png", ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg", ".webp": "image/webp",
                            ".gif": "image/gif", ".bmp": "image/bmp",
                        }
                        for fd in file_data:
                            if isinstance(fd, list) and len(fd) == 2:
                                url_arr, filename = fd[0], fd[1]
                                if isinstance(url_arr, list) and len(url_arr) == 1:
                                    ext = Path(filename).suffix.lower() if isinstance(filename, str) else ""
                                    mime = _MIME_MAP.get(ext, "image/png")
                                    fd[0] = [url_arr[0], 1, None, mime]
                                    fd.extend([None, None, None, None, None, None, [0]])

                    outer[1] = json.dumps(inner)
                    data["f.req"] = json.dumps(outer)
                    kwargs["data"] = data
                except Exception:
                    pass

        return await _orig_request(method, url, **kwargs)

    http.request = patched_request

    # --- Patch _parse_generated_images for new dict-based response format ---
    # Google changed response structure: [12][7][0] (list) -> [12][0]["8"] (dict).
    # See HanaokaYuzu/Gemini-API issues #229, #260, #264.
    import gemini_webapi.client as _gwc
    from gemini_webapi.utils import (
        get_nested_value,
        parse_response_by_frame as _orig_parse,
    )
    from gemini_webapi.types import GeneratedImage
    import orjson as _json

    _orig_parse_images = _gwc._parse_generated_images

    def _patched_parse_images(candidate_data, proxy=None, cookies=None, account_index=0, session_kwargs=None):
        # Try original parser first (old list-based format)
        result = _orig_parse_images(candidate_data, proxy, cookies, account_index, session_kwargs)
        if result:
            return result

        # Fallback: new dict-based format at [12][0]["8"]
        val12 = get_nested_value(candidate_data, [12])
        if not isinstance(val12, list) or not val12:
            return result
        entry = val12[0]
        if not isinstance(entry, dict) or "8" not in entry:
            return result
        generated_images = []
        for gen_img_data in entry["8"]:
            # Structure: [[[null, null, null, [null, 1, "filename.png", "url", ...], ...], ...]]
            url_arr = get_nested_value(gen_img_data, [0, 0, 3])
            if isinstance(url_arr, list) and len(url_arr) >= 4:
                url = url_arr[3]
                title = url_arr[2] or "[Generated Image]"
                token = url_arr[4] if len(url_arr) > 4 else None
                if url and isinstance(url, str) and url.startswith("http"):
                    if token:
                        _image_tokens[url] = token
                    generated_images.append(
                        GeneratedImage(
                            url=url,
                            title=f"[Generated Image]",
                            alt="",
                            proxy=proxy,
                            cookies=cookies,
                            account_index=account_index,
                            session_kwargs=session_kwargs or {},
                        )
                    )
        if generated_images:
            logger.info("Parsed %d images from new dict-based response format", len(generated_images))
        return generated_images

    _gwc._parse_generated_images = _patched_parse_images

    # --- Wrap parse_response_by_frame to capture image download tokens ---
    def _patched_parse(buffer):
        parts, remaining = _orig_parse(buffer)
        for part in parts:
            inner_json_str = get_nested_value(part, [2])
            if not inner_json_str:
                continue
            try:
                part_json = _json.loads(inner_json_str)
                # Capture conversation metadata (cid/rid)
                m_data = get_nested_value(part_json, [1])
                if isinstance(m_data, list) and len(m_data) >= 2 and m_data[0]:
                    if len(_last_metadata) >= 3:
                        _last_metadata[0] = m_data[0]
                        _last_metadata[1] = m_data[1]
                    else:
                        _last_metadata.clear()
                        _last_metadata.extend(m_data)
                # Capture image download tokens + rcid from candidates
                candidates = get_nested_value(part_json, [4], [])
                for cand in candidates:
                    rcid = get_nested_value(cand, [0])
                    if rcid and isinstance(rcid, str) and rcid.startswith("rc_"):
                        if len(_last_metadata) >= 2:
                            if len(_last_metadata) == 2:
                                _last_metadata.append(rcid)
                            else:
                                _last_metadata[2] = rcid
                    # Old format: [12][7][0]
                    for gid in get_nested_value(cand, [12, 7, 0], []):
                        url = get_nested_value(gid, [0, 3, 3])
                        token = get_nested_value(gid, [0, 3, 5])
                        if url and token:
                            _image_tokens[url] = token
                    # New dict format: [12][0]["8"]
                    val12 = get_nested_value(cand, [12])
                    if isinstance(val12, list) and val12 and isinstance(val12[0], dict):
                        for gid in val12[0].get("8", []):
                            url_arr = get_nested_value(gid, [0, 0, 3])
                            if isinstance(url_arr, list) and len(url_arr) >= 5:
                                url, token = url_arr[3], url_arr[4]
                                if url and token:
                                    _image_tokens[url] = token
            except Exception:
                pass
        return parts, remaining

    _gwc.parse_response_by_frame = _patched_parse
    logger.info("Patched GeminiClient with browser-compatible parameters")


def _handle_error(e: Exception) -> str:
    from gemini_webapi import AuthError, APIError, RequestTimeoutError

    if isinstance(e, AuthError):
        return (
            "Error: Authentication failed. Cookies may have expired. "
            "Re-login to gemini.google.com in Chrome, then call gemini_reset."
        )
    if isinstance(e, RequestTimeoutError):
        return "Error: Request timed out. Try again or use a lighter model."
    if isinstance(e, APIError):
        return f"Error: Gemini API error — {e}"
    return f"Error: {type(e).__name__} — {e}"


async def _fetch_download_url(client, token: str, prompt: str, metadata: list, image_index: int = 0) -> str | None:
    """Call c8o8Fe RPC to get a high-resolution (2x) download URL for a generated image.

    Google stores a 2x upscaled version accessible only through this RPC endpoint.
    Returns the download URL or None on failure.
    """
    import orjson as _json
    from gemini_webapi.constants import Endpoint
    from gemini_webapi.utils import parse_response_by_frame, get_nested_value

    cid = metadata[0] if metadata else None
    rid = metadata[1] if len(metadata) > 1 else None
    rcid = metadata[2] if len(metadata) > 2 else None
    if not (rid and rcid and cid):
        logger.warning("c8o8Fe skipped: missing metadata (cid/rid/rcid)")
        return None

    gen_id = _make_gen_id()
    inner_payload = _json.dumps([
        [
            [None, None, None, [None, None, None, None, None, token]],
            [f"http://googleusercontent.com/image_generation_content/{image_index}", image_index],
            None,
            [19, prompt],
            None, None, None, None, None,
            gen_id,
        ],
        [rid, rcid, cid, None, gen_id],
        1, 0, 1,
    ]).decode("utf-8")

    outer_payload = _json.dumps(
        [[["c8o8Fe", inner_payload, None, "generic"]]]
    ).decode("utf-8")

    params: dict = {
        "rpcids": "c8o8Fe",
        "_reqid": client._reqid,
        "rt": "c",
        "source-path": Endpoint.get_source_path(client.account_index),
    }
    client._reqid += 100000
    if client.build_label:
        params["bl"] = client.build_label
    if client.session_id:
        params["f.sid"] = client.session_id

    try:
        resp = await client.client.post(
            Endpoint.get_batch_exec_url(client.account_index),
            params=params,
            data={"at": client.access_token, "f.req": outer_payload},
            headers={
                "x-goog-ext-525001261-jspb": "[1,null,null,null,null,null,null,0,[4,4]]",
                "x-goog-ext-73010989-jspb": "[0]",
            },
            timeout=60,
        )
        if resp.status_code != 200:
            logger.warning("c8o8Fe returned status %d", resp.status_code)
            return None

        text = resp.text
        if text.startswith(")]}'"):
            text = text[4:].lstrip()
        parts, _ = parse_response_by_frame(text)
        # parse_response_by_frame returns each sublist as a separate part:
        # part = ['wrb.fr', 'c8o8Fe', '["url"]', None, None, None, 'generic']
        for part in parts:
            if isinstance(part, list) and len(part) > 2 and part[1] == "c8o8Fe":
                inner_str = part[2]
                if inner_str and isinstance(inner_str, str):
                    inner = _json.loads(inner_str)
                    if isinstance(inner, list) and inner:
                        return inner[0]
        logger.warning("c8o8Fe: no download URL in response (%d parts parsed)", len(parts))
    except Exception as exc:
        logger.warning("c8o8Fe failed: %s", exc)
    return None


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
    conversation_id: Optional[list[str]] = None,
) -> str:
    """Generate or edit images with Gemini.

    Without files: generates a new image from the text prompt.
    With files: edits/transforms the provided image(s) based on the prompt.

    Pass conversation_id from a previous call to continue refining images
    in the same conversation thread (e.g. "make it more dramatic", "add rain").
    You can also use a cid from the Gemini web URL (gemini.google.com/app/{cid}).

    Images are saved to ~/Pictures/gemini/ and full file paths are returned.

    Args:
        prompt: Description of the image to generate, or editing instruction
                (e.g. 'change the background to blue', 'make it a cartoon').
        model: Model name. Defaults to gemini-3.0-flash-thinking
               (Nano Banana 2, supports non-square aspect ratios).
        files: Optional list of file paths to images to edit/transform.
        conversation_id: Optional list of [cid, rid, rcid] from a previous
                         gemini_generate_image response to continue the conversation.
                         Passing just [cid] (from browser URL) also works.

    Returns:
        JSON with generated image paths, conversation_id for continuation, or an error message.
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

        chat = None
        async with _image_lock:
            _image_mode = True
            try:
                if conversation_id:
                    chat = client.start_chat(
                        metadata=conversation_id,
                        model=model or "gemini-3.0-flash-thinking",
                    )
                    response = await chat.send_message(
                        prompt, files=resolved_files or None
                    )
                else:
                    kwargs = {"model": model or "gemini-3.0-flash-thinking"}
                    if resolved_files:
                        kwargs["files"] = resolved_files
                    response = await client.generate_content(prompt, **kwargs)
            finally:
                _image_mode = False

        if not response.images:
            return response.text or "No images were generated. Try rephrasing your prompt."

        # --- Try to get 2x download URLs via c8o8Fe RPC ---
        # Always prefer _last_metadata from monkey-patched response parsing
        # (captures raw stream data needed for c8o8Fe). Fall back to chat metadata.
        if _last_metadata and _last_metadata[0]:
            metadata = list(_last_metadata)
        elif chat:
            metadata = [chat.cid or "", chat.rid or "", chat.rcid or ""]
        else:
            metadata = []
        download_urls: dict[int, str] = {}
        for i, image in enumerate(response.images):
            token = _image_tokens.pop(image.url, None)
            if token and metadata:
                logger.info("Requesting 2x download URL for image %d...", i)
                dl_url = await _fetch_download_url(client, token, prompt, metadata, i)
                if dl_url:
                    download_urls[i] = dl_url
                    logger.info("Got 2x download URL for image %d", i)
        _image_tokens.clear()  # clean up any leftover tokens

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        saved = []

        for i, image in enumerate(response.images):
            # Use 2x upscale URL from c8o8Fe if available
            has_upscale = i in download_urls
            if has_upscale:
                # Use c8o8Fe 2x URL with =s0 for full resolution (not =s2048 which downscales)
                image.url = re.sub(r"=[^/]*$", "", download_urls[i]) + "=s0"

            try:
                filepath = await image.save(
                    path=str(IMAGES_DIR),
                    filename=f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.png",
                    verbose=False,
                    full_size=not has_upscale,  # c8o8Fe already has =s0; preview gets =s2048
                )
            except Exception as save_err:
                logger.warning("Image save failed for %d: %s", i, save_err)
                continue

            if not filepath:
                continue

            try:
                if _remove_watermark(filepath):
                    logger.info("Watermark removed from %s", filepath)
            except Exception as wm_err:
                logger.warning("Watermark removal failed: %s", wm_err)
            title = getattr(image, "title", None) or f"image_{i}"
            saved.append({"title": title, "path": filepath, "dir": str(IMAGES_DIR)})

        # For response: prefer chat metadata (clean cid/rid/rcid), fall back to raw
        if chat:
            conv_id = [chat.cid or "", chat.rid or "", chat.rcid or ""]
        else:
            conv_id = metadata[:3] if metadata and metadata[0] else None
        result = {
            "text": response.text or "",
            "images_saved_to": str(IMAGES_DIR),
            "images": saved,
            "conversation_id": conv_id,
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
    name="gemini_analyze_url",
    annotations={
        "title": "Gemini URL Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gemini_analyze_url(
    url: str,
    ctx: Context,
    prompt: str = "Summarize this content.",
    model: Optional[str] = None,
) -> str:
    """Analyze a URL — YouTube videos, webpages, articles, etc.

    Gemini can watch YouTube videos and read webpages, then answer
    questions about their content.

    Args:
        url: The URL to analyze (YouTube, article, webpage, etc.).
        prompt: Question or instruction about the content
                (e.g. 'Summarize this video', 'What are the key points?').
        model: Model name. Defaults to gemini-3.0-flash.

    Returns:
        Gemini's analysis of the URL content.
    """
    try:
        client = _get_client(ctx)
        full_prompt = f"{prompt}\n\n{url}"
        response = await client.generate_content(
            full_prompt, model=model or DEFAULT_MODEL
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

        account_index = int(os.environ.get("GEMINI_ACCOUNT_INDEX", "0"))
        new_client = GeminiClient(
            secure_1psid=psid, secure_1psidts=psidts or None, account_index=account_index
        )
        await new_client.init(timeout=300, watchdog_timeout=45, auto_close=False, auto_refresh=True)
        _patch_client(new_client)

        ctx.request_context.lifespan_context["gemini_client"] = new_client
        return "Gemini client re-initialised with fresh cookies."

    except Exception as e:
        return _handle_error(e)

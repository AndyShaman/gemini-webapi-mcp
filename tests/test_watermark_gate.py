"""Watermark removal must never paint a dark ✦ ghost where no sparkle exists.

Regression (2026-11-21): Gemini txt2img downloads arrived with no visible ✦ at
the m96 anchor, but a sharp diagonal edge crossed the anchor box. The plane-fit
opacity estimate read the edge as overlay (A≈0.13), the reverse blend stamped a
dark ✦, and the post-check (corr 0.12 → -0.03) didn't catch it. Removal must
require the sparkle to actually be there (shape correlation) before subtracting.
"""
import os
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gemini_webapi_mcp import server as S  # noqa: E402

W, H, LOGO, MARGIN = 1376, 768, 48, 96
X0, Y0 = W - MARGIN - LOGO, H - MARGIN - LOGO


def _smooth_base(seed=0, level=130.0):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = level + 25 * np.sin(xx / 53.0) + 20 * np.cos(yy / 61.0)
    return np.clip(base[..., None] + rng.normal(0, 2, (H, W, 3)), 0, 255).astype(np.float32)


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _real_edge_corner():
    """Bottom-right 256px of a real 1376×768 Gemini frame with NO visible ✦: a
    grey bezel edge over a near-black area crosses the m96 anchor box. The
    pre-fix code fitted A≈0.15 here and stamped a dark ghost (up to 37 levels)."""
    path = os.path.join(FIXTURES, "edge_no_mark_corner_256.png")
    return np.asarray(Image.open(path).convert("RGB"), np.float32)


def _stamp(clean, A=0.27):
    """Forward-blend the white ✦ at the m96 anchor (L = bg + A·shape·(255-bg))."""
    alpha = (S._shape_at(LOGO) * A)[..., None]
    out = clean.copy()
    box = out[Y0:Y0 + LOGO, X0:X0 + LOGO]
    out[Y0:Y0 + LOGO, X0:X0 + LOGO] = box * (1 - alpha) + alpha * 255.0
    return out


def _run_remove(arr):
    fd, p = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(p)
    before = np.asarray(Image.open(p).convert("RGB"), np.float32)
    removed = S._remove_watermark(p)
    after = np.asarray(Image.open(p).convert("RGB"), np.float32)
    os.remove(p)
    return removed, before, after


def test_real_sparkle_is_removed():
    clean = _smooth_base(3)
    removed, _, after = _run_remove(_stamp(clean))
    err = float(np.abs(after[Y0:Y0 + LOGO, X0:X0 + LOGO] - clean[Y0:Y0 + LOGO, X0:X0 + LOGO]).max())
    assert removed, "real ✦ not removed"
    assert err <= 8.0, f"visible residual after removal (max error {err:.1f})"


def test_no_sparkle_on_real_edge_is_left_untouched():
    removed, before, after = _run_remove(_real_edge_corner())
    diff = float(np.abs(after - before).max())
    assert not removed, "removal ran on a frame with no ✦"
    assert diff < 1.0, f"frame without ✦ was modified (max change {diff:.1f} levels: dark ghost)"


def test_real_2x_sparkle_on_busy_frame_still_removed():
    """Real 2x frame (96px ✦ at m64, corr ≈0.55 over busy texture) must still
    pass the presence gate and be removed via the upscaled path."""
    removed, _, _ = _run_remove_2x(os.path.join(FIXTURES, "busy_corner_1280.png"))
    assert removed, "real 2x ✦ no longer removed"


def _run_remove_2x(path):
    import shutil
    fd, p = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    shutil.copy(path, p)
    before = np.asarray(Image.open(p).convert("RGB"), np.float32)
    removed = S._remove_watermark(p, upscaled=True)
    after = np.asarray(Image.open(p).convert("RGB"), np.float32)
    os.remove(p)
    return removed, before, after


def test_no_sparkle_on_smooth_frame_is_left_untouched():
    removed, before, after = _run_remove(_smooth_base(9))
    assert not removed
    assert float(np.abs(after - before).max()) < 1.0

from typing import Any, Dict


REFERENCE_WIDTH = 1920
REFERENCE_HEIGHT = 1080
REFERENCE_ASPECT = REFERENCE_WIDTH / REFERENCE_HEIGHT


def game_viewport(width: int, height: int) -> Dict[str, int]:
    """Return the centered 16:9 game viewport inside a client area."""
    if width <= 0 or height <= 0:
        return {"left": 0, "top": 0, "width": 0, "height": 0}

    if width / height > REFERENCE_ASPECT:
        viewport_width = round(height * REFERENCE_ASPECT)
        return {
            "left": (width - viewport_width) // 2,
            "top": 0,
            "width": viewport_width,
            "height": height,
        }

    viewport_height = round(width / REFERENCE_ASPECT)
    return {
        "left": 0,
        "top": (height - viewport_height) // 2,
        "width": width,
        "height": viewport_height,
    }


def scale_ratio_roi(roi: Dict[str, float], viewport: Dict[str, int]) -> Dict[str, int]:
    return {
        "left": viewport["left"] + round(roi["left"] * viewport["width"]),
        "top": viewport["top"] + round(roi["top"] * viewport["height"]),
        "width": round(roi["width"] * viewport["width"]),
        "height": round(roi["height"] * viewport["height"]),
    }


def scale_pixel_roi(roi: Dict[str, Any], viewport: Dict[str, int]) -> Dict[str, int]:
    return {
        "left": viewport["left"] + round(roi["left"] * viewport["width"] / REFERENCE_WIDTH),
        "top": viewport["top"] + round(roi["top"] * viewport["height"] / REFERENCE_HEIGHT),
        "width": round(roi["width"] * viewport["width"] / REFERENCE_WIDTH),
        "height": round(roi["height"] * viewport["height"] / REFERENCE_HEIGHT),
    }


def scale_roi(roi: Dict[str, Any], client_rect: tuple[int, int, int, int]) -> Dict[str, int]:
    rect_x, rect_y, width, height = client_rect
    viewport = game_viewport(width, height)
    viewport["left"] += rect_x
    viewport["top"] += rect_y
    # Heuristic: if <= 1.0, it's likely a normalized ratio
    if isinstance(roi.get("left"), (float, int)) and roi.get("left", 0) <= 1.0:
        return scale_ratio_roi(roi, viewport)
    return scale_pixel_roi(roi, viewport)

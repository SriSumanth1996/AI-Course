from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "gates" / "animated"
FRAME_SIZE = (240, 300)
TWEEN_COUNT = 4
FRAME_DURATION_MS = 45


def load_rgba(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGBA").resize(FRAME_SIZE, Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float32) / 255.0


def flow_gray(frame: np.ndarray) -> np.ndarray:
    alpha = frame[..., 3:4]
    composite = frame[..., :3] * alpha + (1.0 - alpha)
    gray = cv2.cvtColor((composite * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    return cv2.GaussianBlur(gray, (5, 5), 0)


def optical_flow(start: np.ndarray, end: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    start_gray = flow_gray(start)
    end_gray = flow_gray(end)
    forward = cv2.calcOpticalFlowFarneback(
        start_gray, end_gray, None, 0.5, 5, 25, 4, 7, 1.5, 0
    )
    backward = cv2.calcOpticalFlowFarneback(
        end_gray, start_gray, None, 0.5, 5, 25, 4, 7, 1.5, 0
    )
    return forward, backward


def remap(frame: np.ndarray, flow: np.ndarray, amount: float) -> np.ndarray:
    height, width = frame.shape[:2]
    grid_x, grid_y = np.meshgrid(
        np.arange(width, dtype=np.float32),
        np.arange(height, dtype=np.float32),
    )
    map_x = grid_x - flow[..., 0] * amount
    map_y = grid_y - flow[..., 1] * amount
    return cv2.remap(
        frame,
        map_x,
        map_y,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def premultiply(frame: np.ndarray) -> np.ndarray:
    alpha = frame[..., 3:4]
    return np.concatenate((frame[..., :3] * alpha, alpha), axis=2)


def unpremultiply(frame: np.ndarray) -> np.ndarray:
    alpha = np.clip(frame[..., 3:4], 0.0, 1.0)
    rgb = np.divide(
        frame[..., :3],
        np.maximum(alpha, 1e-5),
        out=np.zeros_like(frame[..., :3]),
        where=alpha > 1e-5,
    )
    return np.concatenate((np.clip(rgb, 0.0, 1.0), alpha), axis=2)


def tween(start: np.ndarray, end: np.ndarray, count: int) -> list[np.ndarray]:
    forward, backward = optical_flow(start, end)
    start_pm = premultiply(start)
    end_pm = premultiply(end)
    frames: list[np.ndarray] = []
    for index in range(1, count + 1):
        progress = index / (count + 1)
        eased = progress * progress * (3.0 - 2.0 * progress)
        start_warp = remap(start_pm, forward, eased)
        end_warp = remap(end_pm, backward, 1.0 - eased)
        mixed = start_warp * (1.0 - eased) + end_warp * eased
        frames.append(unpremultiply(mixed))
    return frames


def to_pillow(frame: np.ndarray) -> Image.Image:
    rgba = (np.clip(frame, 0.0, 1.0) * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def build(provider: str) -> Path:
    poses = [
        load_rgba(ASSETS / f"{provider}-{name}.webp")
        for name in ("ready", "lift", "reach", "open", "stop")
    ]
    motion = [poses[0]]
    for start, end in zip(poses, poses[1:]):
        motion.extend(tween(start, end, TWEEN_COUNT))
        motion.append(end)
    sequence = (
        [poses[0]] * 7
        + motion[1:]
        + [poses[-1]] * 11
        + list(reversed(motion[1:-1]))
        + [poses[0]] * 7
    )
    frames = [to_pillow(frame) for frame in sequence]

    # A single-row sprite lets CSS own the animation clock. That keeps the
    # character's hand frame exactly synchronized with the incoming pulse.
    sprite = Image.new("RGBA", (FRAME_SIZE[0] * len(frames), FRAME_SIZE[1]))
    for index, frame in enumerate(frames):
        sprite.alpha_composite(frame, (index * FRAME_SIZE[0], 0))
    sprite_output = ASSETS / f"{provider}-sprite.webp"
    sprite.save(
        sprite_output,
        "WEBP",
        quality=86,
        method=6,
        exact=True,
    )

    output = ASSETS / f"{provider}-animated.webp"
    frames[0].save(
        output,
        "WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        quality=86,
        method=4,
        exact=True,
        minimize_size=False,
    )
    print(sprite_output)
    return output


if __name__ == "__main__":
    for provider_name in ("openai", "meta"):
        print(build(provider_name))

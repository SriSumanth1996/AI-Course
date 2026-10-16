"""Split the supplied API-error reaction sheet into ten transparent assets."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "gates" / "errors" / "reactions-sheet.png"
OUTPUT = SOURCE.parent
REACTIONS = ("401", "402", "429", "timeout", "5xx")


def build_connection_reaction(provider: str) -> None:
    source = OUTPUT / f"{provider}-connection-source.png"
    image = Image.open(source).convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        raise RuntimeError(f"Connection reaction is empty: {source}")

    cropped = image.crop(bounds)
    padded = Image.new("RGBA", (cropped.width + 24, cropped.height + 24))
    padded.alpha_composite(cropped, (12, 12))
    padded.thumbnail((540, 455), Image.Resampling.LANCZOS)
    target = OUTPUT / f"{provider}-connection.webp"
    padded.save(target, "WEBP", lossless=True, method=6)
    print(f"wrote {target.relative_to(ROOT)} {padded.size}")


def main() -> None:
    sheet = Image.open(SOURCE).convert("RGBA")
    pixels = np.asarray(sheet)
    alpha = pixels[:, :, 3]

    # A small alpha threshold separates the ten supplied reaction groups while
    # retaining their soft antialiased edges through the dilation below.
    count, labels, stats, centers = cv2.connectedComponentsWithStats(
        (alpha > 8).astype(np.uint8), connectivity=8
    )
    groups = [
        index
        for index in range(1, count)
        if int(stats[index, cv2.CC_STAT_AREA]) > 50_000
    ]
    if len(groups) != 10:
        raise RuntimeError(f"Expected 10 reaction groups, found {len(groups)}")

    middle = sheet.height / 2
    top = sorted(
        (index for index in groups if centers[index][1] < middle),
        key=lambda index: centers[index][0],
    )
    bottom = sorted(
        (index for index in groups if centers[index][1] >= middle),
        key=lambda index: centers[index][0],
    )
    if len(top) != 5 or len(bottom) != 5:
        raise RuntimeError("Expected a five-column by two-row reaction sheet")

    kernel = np.ones((3, 3), dtype=np.uint8)
    for provider, row in (("openai", top), ("meta", bottom)):
        for reaction, component in zip(REACTIONS, row, strict=True):
            component_mask = (labels == component).astype(np.uint8)
            component_mask = cv2.dilate(component_mask, kernel, iterations=2).astype(bool)
            isolated = pixels.copy()
            isolated[:, :, 3] = np.where(component_mask, alpha, 0)

            ys, xs = np.nonzero(isolated[:, :, 3])
            left = max(0, int(xs.min()) - 8)
            top_edge = max(0, int(ys.min()) - 8)
            right = min(sheet.width, int(xs.max()) + 9)
            bottom_edge = min(sheet.height, int(ys.max()) + 9)
            asset = Image.fromarray(isolated, "RGBA").crop(
                (left, top_edge, right, bottom_edge)
            )
            target = OUTPUT / f"{provider}-{reaction}.webp"
            asset.save(target, "WEBP", lossless=True, method=6)
            print(f"wrote {target.relative_to(ROOT)} {asset.size}")

    for provider in ("openai", "meta"):
        build_connection_reaction(provider)


if __name__ == "__main__":
    main()

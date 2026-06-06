"""WD14-style image tag extraction facade.

The default implementation is deterministic and lightweight. Replace
``WD14LikeTagger.extract`` with a real ONNX/transformers tagger in production.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Iterable, List, Union


@dataclass
class ImageTags:
    path: str
    tags: List[str]
    confidence: float


class WD14LikeTagger:
    """Extract coarse visual tags from images.

    Real implementation sketch:
      1. Load a WD14-compatible ViT/Swin tagger.
      2. Resize and normalize the image.
      3. Keep tags above threshold and return sorted confidence scores.
    """

    base_tags = [
        "solo",
        "portrait",
        "front view",
        "upper body",
        "natural skin texture",
        "black hair",
        "smiling",
        "casual clothing",
        "indoor background",
        "soft lighting",
    ]

    def extract(self, image_path: Union[str, Path]) -> ImageTags:
        path = Path(image_path)
        digest = self._digest(path)
        variants = self._variant_tags(digest)
        return ImageTags(path=str(path), tags=self.base_tags + variants, confidence=0.82)

    def batch_extract(self, image_paths: Iterable[Union[str, Path]]) -> List[ImageTags]:
        return [self.extract(path) for path in image_paths]

    @staticmethod
    def _digest(path: Path) -> str:
        if path.exists() and path.is_file():
            return hashlib.sha1(path.read_bytes()).hexdigest()
        return hashlib.sha1(str(path).encode("utf-8")).hexdigest()

    @staticmethod
    def _variant_tags(digest: str) -> List[str]:
        palette = [
            ["round face", "clear eyes"],
            ["oval face", "straight nose"],
            ["short hair", "defined jawline"],
            ["long hair", "bright eyes"],
        ]
        return palette[int(digest[:2], 16) % len(palette)]

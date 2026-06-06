"""Dataset preparation utilities for few-shot identity LoRA training."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
from typing import Iterable, List, Optional, Union

from .config import DecoupledTags
from .tagging import WD14LikeTagger
from .semantic import MultimodalSemanticReconstructor


@dataclass
class TrainingSample:
    image_path: str
    caption: str
    tags: DecoupledTags


class FewShotIdentityDatasetBuilder:
    """Build captions with ID/style disentanglement and dropout-ready slots."""

    def __init__(self, tagger: Optional[WD14LikeTagger] = None, reconstructor: Optional[MultimodalSemanticReconstructor] = None):
        self.tagger = tagger or WD14LikeTagger()
        self.reconstructor = reconstructor or MultimodalSemanticReconstructor()

    def build(self, image_paths: Iterable[Union[str, Path]], role: str = "fan") -> List[TrainingSample]:
        samples: List[TrainingSample] = []
        for image_path in image_paths:
            tags = self.reconstructor.reconstruct([self.tagger.extract(image_path)], role=role)
            caption = self.compose_caption(tags)
            samples.append(TrainingSample(image_path=str(image_path), caption=caption, tags=tags))
        return samples

    @staticmethod
    def compose_caption(tags: DecoupledTags) -> str:
        parts = tags.to_prompt_parts()
        return (
            f"identity tokens: {parts['identity']}; "
            f"pose tokens: {parts['pose']}; "
            f"clothing tokens: {parts['clothing']}; "
            f"background tokens: {parts['background']}"
        )

    @staticmethod
    def apply_prompt_dropout(caption: str, dropout: float, rng: random.Random) -> str:
        """Drop non-ID clauses to prevent pose/outfit memorization."""

        clauses = [part.strip() for part in caption.split(";") if part.strip()]
        kept = []
        for clause in clauses:
            is_identity = clause.startswith("identity tokens")
            if is_identity or rng.random() > dropout:
                kept.append(clause)
        return "; ".join(kept)

    @staticmethod
    def perturb_tags(caption: str, noise: float, rng: random.Random) -> str:
        if rng.random() >= noise:
            return caption
        replacements = {
            "front view": "three-quarter view",
            "upper body": "half body",
            "indoor background": "neutral background",
            "casual clothing": "simple outfit",
        }
        for source, target in replacements.items():
            caption = caption.replace(source, target)
        return caption

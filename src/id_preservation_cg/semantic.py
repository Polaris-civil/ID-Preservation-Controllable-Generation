"""Multimodal semantic reconstruction and tag decoupling."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable, List

from .config import DecoupledTags
from .tagging import ImageTags


class MultimodalSemanticReconstructor:
    """Reconstruct WD14-style tags into controllable semantic slots.

    Production usage can call Qwen-VL, DeepSeek-VL, or another VLM here:

    ``prompt = f"Given image tags {tags}, split identity, pose, clothing, background..."``

    The offline implementation below keeps the same contract and is suitable for
    tests, examples, and prompt manifest generation.
    """

    identity_keywords = {"face", "eyes", "nose", "jawline", "hair", "skin"}
    pose_keywords = {"front view", "upper body", "sitting", "standing", "pose", "smiling"}
    clothing_keywords = {"clothing", "dress", "jacket", "shirt", "uniform"}
    background_keywords = {"background", "indoor", "outdoor", "studio", "street", "lighting"}

    def reconstruct(self, image_tags: Iterable[ImageTags], role: str = "fan") -> DecoupledTags:
        flat_tags = self._flatten(image_tags)
        slots = DecoupledTags()
        for tag in flat_tags:
            lowered = tag.lower()
            if any(key in lowered for key in self.identity_keywords):
                slots.identity.append(f"{role}: {tag}")
            elif any(key in lowered for key in self.pose_keywords):
                slots.pose.append(tag)
            elif any(key in lowered for key in self.clothing_keywords):
                slots.clothing.append(tag)
            elif any(key in lowered for key in self.background_keywords):
                slots.background.append(tag)

        slots.identity = self._dedupe(slots.identity) or [f"{role}: consistent facial identity"]
        slots.pose = self._dedupe(slots.pose) or ["natural standing pose"]
        slots.clothing = self._dedupe(slots.clothing) or ["customizable outfit"]
        slots.background = self._dedupe(slots.background) or ["customizable scene"]
        return slots

    def explain(self, tags: DecoupledTags) -> dict:
        payload = asdict(tags)
        payload["rationale"] = (
            "Identity tokens are separated from pose, clothing, and background so "
            "LoRA learns stable facial/person features instead of overfitting to a "
            "fixed outfit or scene."
        )
        return payload

    @staticmethod
    def _flatten(image_tags: Iterable[ImageTags]) -> List[str]:
        tags: List[str] = []
        for item in image_tags:
            tags.extend(item.tags)
        return tags

    @staticmethod
    def _dedupe(items: Iterable[str]) -> List[str]:
        seen = set()
        out = []
        for item in items:
            if item not in seen:
                out.append(item)
                seen.add(item)
        return out

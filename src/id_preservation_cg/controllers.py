"""Composable controllers for ID, pose, outfit, and scene constraints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ControllerOutput:
    name: str
    enabled: bool
    weight: float
    summary: str
    payload: Dict[str, str]


class BaseController:
    name = "base"

    def __init__(self, enabled: bool = True, weight: float = 1.0):
        self.enabled = enabled
        self.weight = weight

    def apply(self, context: dict) -> ControllerOutput:
        raise NotImplementedError


class IPAdapterController(BaseController):
    name = "ip_adapter"

    def apply(self, context: dict) -> ControllerOutput:
        refs = context.get("fan_refs", []) + context.get("celebrity_refs", [])
        return ControllerOutput(
            name=self.name,
            enabled=self.enabled,
            weight=self.weight,
            summary="Constrains face structure and identity similarity from reference images.",
            payload={"reference_count": str(len(refs))},
        )


class ControlNetPoseController(BaseController):
    name = "controlnet_openpose"

    def apply(self, context: dict) -> ControllerOutput:
        pose = context.get("pose_image") or ""
        exists = bool(pose and Path(pose).exists())
        return ControllerOutput(
            name=self.name,
            enabled=self.enabled,
            weight=self.weight,
            summary="Guides body layout and action using OpenPose-compatible pose input.",
            payload={"pose_image": pose, "pose_exists": str(exists)},
        )


class StyleController(BaseController):
    name = "redux_or_style_lora"

    def apply(self, context: dict) -> ControllerOutput:
        return ControllerOutput(
            name=self.name,
            enabled=self.enabled,
            weight=self.weight,
            summary="Transfers outfit, background, and rendering style without binding them to identity.",
            payload={
                "clothing_prompt": context.get("clothing_prompt", ""),
                "scene_prompt": context.get("scene_prompt", ""),
            },
        )


class ControllerStack:
    """A small orchestrator that lets callers enable or disable each module."""

    def __init__(self, controllers: Optional[List[BaseController]] = None):
        self.controllers = controllers or []

    def run(self, context: dict) -> List[ControllerOutput]:
        outputs = []
        for controller in self.controllers:
            if controller.enabled:
                outputs.append(controller.apply(context))
        return outputs

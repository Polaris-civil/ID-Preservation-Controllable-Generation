"""End-to-end controllable generation pipeline."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from .backends import backend_for_request
from .config import GenerationRequest, save_json
from .controllers import ControllerStack, ControlNetPoseController, IPAdapterController, StyleController
from .semantic import MultimodalSemanticReconstructor
from .tagging import WD14LikeTagger
from .validation import validate_generation_request


class ControllableGenerationPipeline:
    """Generate fan-celebrity photos with modular ID and control adapters."""

    def __init__(self, tagger: Optional[WD14LikeTagger] = None, reconstructor: Optional[MultimodalSemanticReconstructor] = None):
        self.tagger = tagger or WD14LikeTagger()
        self.reconstructor = reconstructor or MultimodalSemanticReconstructor()

    def generate(self, request: GenerationRequest) -> Dict[str, str]:
        validate_generation_request(request)
        fan_tags = self.reconstructor.reconstruct(self.tagger.batch_extract(request.fan_refs), role="fan")
        celebrity_tags = self.reconstructor.reconstruct(self.tagger.batch_extract(request.celebrity_refs), role="celebrity")
        controllers = self._build_controllers(request).run(asdict(request))
        prompt = self._compose_prompt(request, fan_tags.to_prompt_parts(), celebrity_tags.to_prompt_parts())

        output_path = Path(request.output_path)
        backend_result = backend_for_request(request).render(request, prompt, controllers, output_path)
        manifest_path = output_path.with_suffix(".manifest.json")
        save_json(
            manifest_path,
            {
                "request": asdict(request),
                "prompt": prompt,
                "fan_tags": asdict(fan_tags),
                "celebrity_tags": asdict(celebrity_tags),
                "controllers": [asdict(item) for item in controllers],
                "backend": request.model.backend,
                "backend_result": backend_result,
                "output": str(output_path),
            },
        )
        return {"image": str(output_path), "manifest": str(manifest_path), "prompt": prompt}

    @staticmethod
    def _build_controllers(request: GenerationRequest) -> ControllerStack:
        controls = request.controls
        return ControllerStack(
            [
                IPAdapterController(enabled=controls.use_ip_adapter, weight=controls.ip_adapter_weight),
                ControlNetPoseController(enabled=controls.use_controlnet, weight=controls.controlnet_weight),
                StyleController(enabled=controls.use_style_lora, weight=controls.style_weight),
            ]
        )

    @staticmethod
    def _compose_prompt(request: GenerationRequest, fan: Dict[str, str], celebrity: Dict[str, str]) -> str:
        clauses: List[str] = [
            request.prompt,
            "two-person realistic photo",
            f"fan identity: {fan['identity']}",
            f"celebrity identity: {celebrity['identity']}",
            request.clothing_prompt or f"outfit: {fan['clothing']}",
            request.scene_prompt or f"scene: {fan['background']}",
            "consistent faces, natural interaction, coherent lighting",
        ]
        return ", ".join(part for part in clauses if part)

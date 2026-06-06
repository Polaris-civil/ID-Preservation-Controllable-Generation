"""Generation backend adapters.

The mock backend is the default offline implementation. The ComfyUI backend
prepares a real API payload and can submit it when ``submit_comfyui_job`` is
enabled in ``ModelConfig``.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Dict, List, Protocol
from urllib import request as urlrequest

from .config import GenerationRequest


class GenerationBackend(Protocol):
    def render(self, request: GenerationRequest, prompt: str, controllers: List[object], output_path: Path) -> Dict[str, str]:
        """Render or enqueue a generation job and return backend metadata."""


class MockSvgBackend:
    """Deterministic SVG renderer for local tests and documentation demos."""

    def render(self, request: GenerationRequest, prompt: str, controllers: List[object], output_path: Path) -> Dict[str, str]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_svg_preview(output_path, prompt, controllers)
        return {"backend": "mock", "mode": "offline_svg", "image": str(output_path)}

    @staticmethod
    def _write_svg_preview(output_path: Path, prompt: str, controllers: List[object]) -> None:
        escaped_prompt = (
            prompt.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        controller_text = ", ".join(getattr(item, "name", "controller") for item in controllers) or "none"
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="768" viewBox="0 0 1024 768">
  <rect width="1024" height="768" fill="#f4f1ea"/>
  <rect x="0" y="510" width="1024" height="258" fill="#d7e4df"/>
  <circle cx="385" cy="265" r="88" fill="#d39b72"/>
  <circle cx="632" cy="265" r="88" fill="#c58b65"/>
  <path d="M250 650 C290 470, 480 470, 520 650 Z" fill="#375a7f"/>
  <path d="M506 650 C546 470, 736 470, 776 650 Z" fill="#8b3f47"/>
  <circle cx="355" cy="250" r="9" fill="#202020"/>
  <circle cx="415" cy="250" r="9" fill="#202020"/>
  <circle cx="602" cy="250" r="9" fill="#202020"/>
  <circle cx="662" cy="250" r="9" fill="#202020"/>
  <path d="M350 305 Q385 330 420 305" stroke="#552f2f" stroke-width="8" fill="none" stroke-linecap="round"/>
  <path d="M597 305 Q632 330 667 305" stroke="#552f2f" stroke-width="8" fill="none" stroke-linecap="round"/>
  <text x="512" y="70" font-family="Arial, sans-serif" font-size="34" text-anchor="middle" fill="#1f2933">ID-Preservation Controllable Generation</text>
  <text x="512" y="720" font-family="Arial, sans-serif" font-size="20" text-anchor="middle" fill="#1f2933">controllers: {controller_text}</text>
  <foreignObject x="94" y="100" width="836" height="90">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial,sans-serif;font-size:18px;color:#1f2933;text-align:center;">{escaped_prompt}</div>
  </foreignObject>
</svg>
"""
        output_path.write_text(svg, encoding="utf-8")


class ComfyUIBackend:
    """Prepare and optionally submit a ComfyUI prompt job.

    The bundled workflow is intentionally a template. Local ComfyUI node names
    vary by extension version, so this backend writes the exact API payload next
    to the requested output for review before submission.
    """

    def render(self, request: GenerationRequest, prompt: str, controllers: List[object], output_path: Path) -> Dict[str, str]:
        payload = self._build_payload(request, prompt, controllers)
        payload_path = output_path.with_suffix(".comfyui_payload.json")
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        result = {"backend": "comfyui", "payload": str(payload_path), "submitted": "false"}
        if request.model.submit_comfyui_job:
            response = self._submit(request.model.comfyui_url, payload)
            response_path = output_path.with_suffix(".comfyui_response.json")
            response_path.write_text(json.dumps(response, indent=2, ensure_ascii=False), encoding="utf-8")
            result.update({"submitted": "true", "response": str(response_path)})
        return result

    @staticmethod
    def _build_payload(request: GenerationRequest, prompt: str, controllers: List[object]) -> Dict[str, object]:
        return {
            "client_id": "id-preservation-cg",
            "prompt": {
                "workflow_template": request.model.comfyui_workflow,
                "positive_prompt": prompt,
                "negative_prompt": request.negative_prompt,
                "seed": request.model.seed,
                "base_model": request.model.base_model,
                "fan_refs": request.fan_refs,
                "celebrity_refs": request.celebrity_refs,
                "pose_image": request.pose_image,
                "controllers": [asdict(item) for item in controllers],
            },
        }

    @staticmethod
    def _submit(base_url: str, payload: Dict[str, object]) -> Dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(
            base_url.rstrip("/") + "/prompt",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))


def backend_for_request(request: GenerationRequest) -> GenerationBackend:
    backend = request.model.backend.lower()
    if backend == "mock":
        return MockSvgBackend()
    if backend == "comfyui":
        return ComfyUIBackend()
    raise ValueError(f"Unsupported backend '{request.model.backend}'. Expected 'mock' or 'comfyui'.")

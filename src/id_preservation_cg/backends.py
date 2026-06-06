"""Generation backend adapters.

The mock backend is the default offline implementation. The ComfyUI backend
prepares a real API payload and can submit it when ``submit_comfyui_job`` is
enabled in ``ModelConfig``.
"""

from __future__ import annotations

from dataclasses import asdict
import json
import mimetypes
from pathlib import Path
import time
import uuid
from typing import Any, Dict, List, Protocol, Tuple
from urllib import parse as urlparse
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
    """Submit real ComfyUI API jobs.

    If ``ModelConfig.comfyui_workflow`` points to an API workflow, placeholders
    such as ``{{positive_prompt}}`` and ``{{pose_image_upload}}`` are replaced.
    If it points to the human-readable template bundled with this project, the
    backend falls back to a vanilla ComfyUI txt2img API graph.
    """

    def render(self, request: GenerationRequest, prompt: str, controllers: List[object], output_path: Path) -> Dict[str, str]:
        payload = self._build_payload(request, prompt, controllers)
        payload_path = output_path.with_suffix(".comfyui_payload.json")
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        result = {"backend": "comfyui", "payload": str(payload_path), "submitted": "false"}
        if request.model.submit_comfyui_job:
            client = ComfyUIClient(request.model.comfyui_url)
            response = client.queue_prompt(payload)
            response_path = output_path.with_suffix(".comfyui_response.json")
            response_path.write_text(json.dumps(response, indent=2, ensure_ascii=False), encoding="utf-8")
            prompt_id = str(response["prompt_id"])
            history = client.wait_for_history(
                prompt_id,
                timeout_seconds=request.model.comfyui_timeout,
                poll_interval=request.model.comfyui_poll_interval,
            )
            history_path = output_path.with_suffix(".comfyui_history.json")
            history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
            result.update({"submitted": "true", "prompt_id": prompt_id, "response": str(response_path), "history": str(history_path)})
            if request.model.download_comfyui_output:
                downloaded = client.download_first_output(history, output_path)
                result["downloaded_image"] = str(downloaded)
        return result

    def _build_payload(self, request: GenerationRequest, prompt: str, controllers: List[object]) -> Dict[str, object]:
        workflow, uploaded = self._prepare_workflow(request, prompt)
        return {
            "client_id": f"id-preservation-cg-{uuid.uuid4().hex}",
            "prompt": workflow,
            "extra_data": {
                "extra_pnginfo": {
                    "idpcg": {
                        "positive_prompt": prompt,
                        "negative_prompt": request.negative_prompt,
                        "seed": request.model.seed,
                        "base_model": request.model.base_model,
                        "fan_refs": request.fan_refs,
                        "celebrity_refs": request.celebrity_refs,
                        "pose_image": request.pose_image,
                        "uploaded_images": uploaded,
                        "controllers": [asdict(item) for item in controllers],
                    }
                }
            },
        }

    def _prepare_workflow(self, request: GenerationRequest, prompt: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
        client = ComfyUIClient(request.model.comfyui_url)
        uploaded = self._upload_available_inputs(client, request) if request.model.submit_comfyui_job else {}
        workflow = self._load_api_workflow(request)
        variables = {
            "positive_prompt": prompt,
            "negative_prompt": request.negative_prompt,
            "seed": request.model.seed,
            "checkpoint": request.model.base_model,
            "width": request.model.width,
            "height": request.model.height,
            "batch_size": request.model.batch_size,
            "steps": request.model.steps,
            "cfg": request.model.cfg,
            "sampler_name": request.model.sampler_name,
            "scheduler": request.model.scheduler,
            "filename_prefix": Path(request.output_path).stem or "idpcg_result",
            "pose_image_upload": uploaded.get("pose_image", request.pose_image or ""),
            "fan_ref_upload": uploaded.get("fan_refs_0", request.fan_refs[0] if request.fan_refs else ""),
            "celebrity_ref_upload": uploaded.get("celebrity_refs_0", request.celebrity_refs[0] if request.celebrity_refs else ""),
            "lora_name": request.model.lora_name,
            "lora_strength_model": request.model.lora_strength_model,
            "lora_strength_clip": request.model.lora_strength_clip,
            "controlnet_name": request.model.controlnet_name,
            "controlnet_strength": request.model.controlnet_strength,
            "controlnet_start_percent": request.model.controlnet_start_percent,
            "controlnet_end_percent": request.model.controlnet_end_percent,
            "ip_adapter_name": request.model.ip_adapter_name,
            "ip_adapter_weight": request.model.ip_adapter_weight,
            "clip_vision_name": request.model.clip_vision_name,
        }
        return _replace_placeholders(workflow, variables), uploaded

    @staticmethod
    def _upload_available_inputs(client: "ComfyUIClient", request: GenerationRequest) -> Dict[str, str]:
        uploaded: Dict[str, str] = {}
        for index, image_path in enumerate(request.fan_refs):
            path = Path(image_path)
            if path.exists() and path.is_file():
                uploaded[f"fan_refs_{index}"] = client.upload_image(path)
        for index, image_path in enumerate(request.celebrity_refs):
            path = Path(image_path)
            if path.exists() and path.is_file():
                uploaded[f"celebrity_refs_{index}"] = client.upload_image(path)
        if request.pose_image:
            path = Path(request.pose_image)
            if path.exists() and path.is_file():
                uploaded["pose_image"] = client.upload_image(path)
        return uploaded

    @staticmethod
    def _load_api_workflow(request: GenerationRequest) -> Dict[str, Any]:
        workflow_path = Path(request.model.comfyui_workflow)
        if workflow_path.exists():
            data = json.loads(workflow_path.read_text(encoding="utf-8"))
            if _looks_like_comfyui_api_prompt(data):
                return data
        return _default_txt2img_workflow()


class ComfyUIClient:
    """Minimal ComfyUI HTTP API client using the Python standard library."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def queue_prompt(self, payload: Dict[str, object]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(
            self.base_url + "/prompt",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def wait_for_history(self, prompt_id: str, timeout_seconds: int = 600, poll_interval: float = 1.0) -> Dict[str, Any]:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(poll_interval)
        raise TimeoutError(f"Timed out waiting for ComfyUI prompt_id={prompt_id}")

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        with urlrequest.urlopen(self.base_url + "/history/" + urlparse.quote(prompt_id), timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def system_stats(self) -> Dict[str, Any]:
        with urlrequest.urlopen(self.base_url + "/system_stats", timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def upload_image(self, path: Path) -> str:
        boundary = "----idpcg" + uuid.uuid4().hex
        filename = path.name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        body = _multipart_form_data(
            boundary,
            fields={"type": "input", "overwrite": "true"},
            files={"image": (filename, content_type, path.read_bytes())},
        )
        req = urlrequest.Request(
            self.base_url + "/upload/image",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        subfolder = result.get("subfolder", "")
        name = result.get("name", filename)
        return f"{subfolder}/{name}" if subfolder else name

    def download_first_output(self, history: Dict[str, Any], target_path: Path) -> Path:
        output = _first_image_output(history)
        query = urlparse.urlencode(
            {
                "filename": output["filename"],
                "subfolder": output.get("subfolder", ""),
                "type": output.get("type", "output"),
            }
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with urlrequest.urlopen(self.base_url + "/view?" + query, timeout=60) as response:
            target_path.write_bytes(response.read())
        return target_path


def _looks_like_comfyui_api_prompt(data: Dict[str, Any]) -> bool:
    return bool(data) and all(isinstance(value, dict) and "class_type" in value and "inputs" in value for value in data.values())


def _default_txt2img_workflow() -> Dict[str, Any]:
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "{{checkpoint}}"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": "{{positive_prompt}}"},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": "{{negative_prompt}}"},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": "{{width}}", "height": "{{height}}", "batch_size": "{{batch_size}}"},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": "{{seed}}",
                "steps": "{{steps}}",
                "cfg": "{{cfg}}",
                "sampler_name": "{{sampler_name}}",
                "scheduler": "{{scheduler}}",
                "denoise": 1.0,
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"images": ["6", 0], "filename_prefix": "{{filename_prefix}}"},
        },
    }


def _replace_placeholders(value: Any, variables: Dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_placeholders(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_placeholders(item, variables) for item in value]
    if isinstance(value, str):
        if value.startswith("{{") and value.endswith("}}") and value[2:-2] in variables:
            return variables[value[2:-2]]
        for key, replacement in variables.items():
            value = value.replace("{{" + key + "}}", str(replacement))
    return value


def _multipart_form_data(boundary: str, fields: Dict[str, str], files: Dict[str, Tuple[str, str, bytes]]) -> bytes:
    chunks: List[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for name, (filename, content_type, content) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                content,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def _first_image_output(history: Dict[str, Any]) -> Dict[str, str]:
    for node_output in history.get("outputs", {}).values():
        images = node_output.get("images", [])
        if images:
            return images[0]
    raise RuntimeError("ComfyUI history does not contain an image output.")


def backend_for_request(request: GenerationRequest) -> GenerationBackend:
    backend = request.model.backend.lower()
    if backend == "mock":
        return MockSvgBackend()
    if backend == "comfyui":
        return ComfyUIBackend()
    raise ValueError(f"Unsupported backend '{request.model.backend}'. Expected 'mock' or 'comfyui'.")

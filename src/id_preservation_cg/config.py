"""Configuration objects for training and generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ModelConfig:
    """Base model and adapter configuration.

    ``backend`` is intentionally string-based so local deployments can point to
    SDXL, HunyuanDiT, or a custom ComfyUI service without changing public APIs.
    """

    backend: str = "mock"
    base_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    device: str = "auto"
    dtype: str = "fp16"
    seed: int = 42
    comfyui_url: str = "http://127.0.0.1:8188"
    comfyui_workflow: str = "workflows/comfyui_workflow.json"
    submit_comfyui_job: bool = False
    download_comfyui_output: bool = True
    comfyui_timeout: int = 600
    comfyui_poll_interval: float = 1.0
    width: int = 512
    height: int = 512
    batch_size: int = 1
    steps: int = 25
    cfg: float = 7.0
    sampler_name: str = "dpmpp_2m"
    scheduler: str = "karras"
    lora_name: str = ""
    lora_strength_model: float = 0.8
    lora_strength_clip: float = 0.8
    controlnet_name: str = ""
    controlnet_strength: float = 0.85
    controlnet_start_percent: float = 0.0
    controlnet_end_percent: float = 1.0
    ip_adapter_name: str = ""
    ip_adapter_weight: float = 0.75
    clip_vision_name: str = ""


@dataclass
class LoraConfig:
    """LoRA training knobs for few-shot identity learning."""

    rank: int = 16
    alpha: int = 16
    learning_rate: float = 1e-4
    max_steps: int = 800
    train_batch_size: int = 1
    prompt_dropout: float = 0.15
    tag_noise: float = 0.1
    output_dir: str = "checkpoints/fan_lora"


@dataclass
class ControlConfig:
    """Switches for modular generation controllers."""

    use_lora: bool = True
    use_ip_adapter: bool = True
    use_controlnet: bool = True
    use_style_lora: bool = False
    ip_adapter_weight: float = 0.75
    controlnet_weight: float = 0.85
    style_weight: float = 0.55


@dataclass
class DecoupledTags:
    """Semantic slots used to avoid entangling identity with pose/style."""

    identity: List[str] = field(default_factory=list)
    pose: List[str] = field(default_factory=list)
    clothing: List[str] = field(default_factory=list)
    background: List[str] = field(default_factory=list)

    def to_prompt_parts(self) -> Dict[str, str]:
        return {
            "identity": ", ".join(self.identity),
            "pose": ", ".join(self.pose),
            "clothing": ", ".join(self.clothing),
            "background": ", ".join(self.background),
        }


@dataclass
class GenerationRequest:
    """Input bundle for one controllable generation run."""

    fan_refs: List[str]
    celebrity_refs: List[str] = field(default_factory=list)
    pose_image: Optional[str] = None
    prompt: str = "a fan and a celebrity taking a realistic photo together"
    negative_prompt: str = "low quality, blurry, distorted face, extra fingers"
    clothing_prompt: str = ""
    scene_prompt: str = ""
    output_path: str = "outputs/result.svg"
    controls: ControlConfig = field(default_factory=ControlConfig)
    model: ModelConfig = field(default_factory=ModelConfig)


def save_json(path: Union[str, Path], payload: Any) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "__dataclass_fields__"):
        payload = asdict(payload)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_mapping(path: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON or YAML configuration without making YAML a hard dependency."""

    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".json":
        return load_json(source)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install PyYAML to load YAML config files: pip install pyyaml") from exc
        return yaml.safe_load(source.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported config extension: {source.suffix}")


def generation_request_from_dict(data: Dict[str, Any]) -> GenerationRequest:
    """Create a ``GenerationRequest`` from a nested config mapping."""

    allowed = {item.name for item in fields(GenerationRequest)}
    payload = {key: value for key, value in data.items() if key in allowed}
    payload["controls"] = _dataclass_from_dict(ControlConfig, data.get("controls", {}))
    payload["model"] = _dataclass_from_dict(ModelConfig, data.get("model", {}))
    return GenerationRequest(**payload)


def load_generation_request(path: Union[str, Path]) -> GenerationRequest:
    return generation_request_from_dict(load_mapping(path))


def _dataclass_from_dict(cls: type, data: Dict[str, Any]) -> Any:
    allowed = {item.name for item in fields(cls)}
    return cls(**{key: value for key, value in data.items() if key in allowed})

"""Input validation for training and generation requests."""

from __future__ import annotations

from .config import GenerationRequest, LoraConfig


def validate_generation_request(request: GenerationRequest) -> None:
    if not request.fan_refs:
        raise ValueError("GenerationRequest.fan_refs must contain at least one reference image.")
    for name, value in {
        "ip_adapter_weight": request.controls.ip_adapter_weight,
        "controlnet_weight": request.controls.controlnet_weight,
        "style_weight": request.controls.style_weight,
    }.items():
        if value < 0 or value > 2:
            raise ValueError(f"{name} must be between 0 and 2, got {value}.")
    if request.model.backend.lower() not in {"mock", "comfyui"}:
        raise ValueError(f"Unsupported backend: {request.model.backend}")


def validate_lora_config(config: LoraConfig) -> None:
    if config.rank <= 0:
        raise ValueError("LoRA rank must be positive.")
    if config.alpha <= 0:
        raise ValueError("LoRA alpha must be positive.")
    if config.max_steps <= 0:
        raise ValueError("LoRA max_steps must be positive.")
    if not 0 <= config.prompt_dropout <= 1:
        raise ValueError("prompt_dropout must be between 0 and 1.")
    if not 0 <= config.tag_noise <= 1:
        raise ValueError("tag_noise must be between 0 and 1.")

"""ID-preserving controllable generation toolkit.

The package ships with an offline mock backend so the repository can be
installed and exercised without downloading multi-GB model weights. Real model
adapters can be added behind the same interfaces in ``pipeline.py`` and
``lora.py``.
"""

from .config import GenerationRequest, LoraConfig, ModelConfig, generation_request_from_dict, load_generation_request
from .pipeline import ControllableGenerationPipeline

__all__ = [
    "ControllableGenerationPipeline",
    "GenerationRequest",
    "LoraConfig",
    "ModelConfig",
    "generation_request_from_dict",
    "load_generation_request",
]

__version__ = "0.1.0"

"""Production-oriented SDXL LoRA training skeleton.

This file is intentionally explicit rather than magical. It documents where the
offline dataset/caption preparation plugs into a real Diffusers training loop.
Install heavy dependencies first:

    pip install -e ".[full]"

Then replace the marked pseudocode blocks with the exact Diffusers version used
by your environment.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from id_preservation_cg.config import LoraConfig
from id_preservation_cg.lora import LoraTrainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare captions for a real SDXL LoRA job")
    parser.add_argument("images", nargs="+")
    parser.add_argument("--output-dir", default="checkpoints/fan_lora")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--alpha", type=int, default=16)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--trigger-token", default="fan_person")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = LoraConfig(
        output_dir=args.output_dir,
        rank=args.rank,
        alpha=args.alpha,
        max_steps=args.max_steps,
    )
    manifest = LoraTrainer(config).train(args.images, trigger_token=args.trigger_token)
    print(f"Prepared offline training manifest: {manifest}")
    print("Next production steps:")
    print("1. Load the manifest captions into your Diffusers Dataset.")
    print("2. Load SDXL/HunyuanDiT and inject LoRA modules with the requested rank/alpha.")
    print("3. Train adapter layers only, save adapter_model.safetensors to the output directory.")
    print(f"4. Use {Path(args.output_dir) / 'adapter_model.safetensors'} in ComfyUI or the Python backend.")


if __name__ == "__main__":
    main()

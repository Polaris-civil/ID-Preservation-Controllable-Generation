"""Command line interface for the ID-preserving generation workflow."""

from __future__ import annotations

import argparse
from importlib import resources
import json
from pathlib import Path
from urllib.error import URLError
from typing import List, Optional

from .backends import ComfyUIClient
from .config import ControlConfig, GenerationRequest, LoraConfig, load_generation_request
from .lora import LoraTrainer
from .pipeline import ControllableGenerationPipeline
from .semantic import MultimodalSemanticReconstructor
from .tagging import WD14LikeTagger


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def cmd_tag(args: argparse.Namespace) -> int:
    tagger = WD14LikeTagger()
    reconstructor = MultimodalSemanticReconstructor()
    tags = tagger.batch_extract(args.images)
    decoupled = reconstructor.reconstruct(tags, role=args.role)
    payload = {
        "raw": [item.__dict__ for item in tags],
        "decoupled": reconstructor.explain(decoupled),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_train_lora(args: argparse.Namespace) -> int:
    trainer = LoraTrainer(
        LoraConfig(
            rank=args.rank,
            alpha=args.alpha,
            learning_rate=args.learning_rate,
            max_steps=args.max_steps,
            prompt_dropout=args.prompt_dropout,
            tag_noise=args.tag_noise,
            output_dir=args.output_dir,
        )
    )
    manifest = trainer.train(args.images, trigger_token=args.trigger_token)
    print(f"LoRA manifest written to {manifest}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    if args.config:
        request = load_generation_request(args.config)
        if args.output:
            request.output_path = args.output
    else:
        request = GenerationRequest(
            fan_refs=args.fan_refs,
            celebrity_refs=args.celebrity_refs,
            pose_image=args.pose_image,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            clothing_prompt=args.clothing_prompt,
            scene_prompt=args.scene_prompt,
            output_path=args.output,
            controls=ControlConfig(
                use_lora=not args.disable_lora,
                use_ip_adapter=not args.disable_ip_adapter,
                use_controlnet=not args.disable_controlnet,
                use_style_lora=args.use_style_lora,
                ip_adapter_weight=args.ip_adapter_weight,
                controlnet_weight=args.controlnet_weight,
                style_weight=args.style_weight,
            ),
        )
    result = ControllableGenerationPipeline().generate(request)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_workflow(args: argparse.Namespace) -> int:
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    workflow_files = {
        "visual": "comfyui_workflow.json",
        "api": "comfyui_api_txt2img.json",
        "lora-openpose": "comfyui_api_lora_openpose.json",
    }
    filename = workflow_files[args.kind]
    try:
        text = resources.files("id_preservation_cg.assets").joinpath(filename).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        source = Path(__file__).resolve().parents[2] / "workflows" / filename
        if not source.exists():
            raise FileNotFoundError(f"Workflow template not found: {source}")
        text = source.read_text(encoding="utf-8")
    target.write_text(text, encoding="utf-8")
    print(f"ComfyUI workflow copied to {target}")
    return 0


def cmd_comfyui_check(args: argparse.Namespace) -> int:
    try:
        stats = ComfyUIClient(args.url).system_stats()
    except URLError as exc:
        print(json.dumps({"ok": False, "url": args.url, "error": str(exc)}, indent=2, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "url": args.url, "system_stats": stats}, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="idpcg", description="ID-preserving controllable generation toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tag = subparsers.add_parser("tag", help="Extract and decouple tags from reference images")
    tag.add_argument("images", nargs="+")
    tag.add_argument("--role", default="fan")
    tag.set_defaults(func=cmd_tag)

    train = subparsers.add_parser("train-lora", help="Prepare or run few-shot LoRA identity training")
    train.add_argument("images", nargs="+")
    train.add_argument("--trigger-token", default="fan_person")
    train.add_argument("--rank", type=int, default=16)
    train.add_argument("--alpha", type=int, default=16)
    train.add_argument("--learning-rate", type=float, default=1e-4)
    train.add_argument("--max-steps", type=int, default=800)
    train.add_argument("--prompt-dropout", type=float, default=0.15)
    train.add_argument("--tag-noise", type=float, default=0.1)
    train.add_argument("--output-dir", default="checkpoints/fan_lora")
    train.set_defaults(func=cmd_train_lora)

    gen = subparsers.add_parser("generate", help="Run controllable fan-celebrity generation")
    gen.add_argument("--config", help="Path to a JSON/YAML generation request")
    gen.add_argument("--fan-refs", nargs="+")
    gen.add_argument("--celebrity-refs", nargs="*", default=[])
    gen.add_argument("--pose-image")
    gen.add_argument("--prompt", default="a fan and a celebrity taking a realistic photo together")
    gen.add_argument("--negative-prompt", default="low quality, blurry, distorted face")
    gen.add_argument("--clothing-prompt", default="")
    gen.add_argument("--scene-prompt", default="")
    gen.add_argument("--output", default=None)
    gen.add_argument("--disable-lora", action="store_true")
    gen.add_argument("--disable-ip-adapter", action="store_true")
    gen.add_argument("--disable-controlnet", action="store_true")
    gen.add_argument("--use-style-lora", action="store_true")
    gen.add_argument("--ip-adapter-weight", type=float, default=0.75)
    gen.add_argument("--controlnet-weight", type=float, default=0.85)
    gen.add_argument("--style-weight", type=float, default=0.55)
    gen.set_defaults(func=cmd_generate)

    workflow = subparsers.add_parser("workflow", help="Copy the example ComfyUI workflow JSON")
    workflow.add_argument("--output", default="outputs/comfyui_workflow.json")
    workflow.add_argument("--kind", choices=["visual", "api", "lora-openpose"], default="visual")
    workflow.set_defaults(func=cmd_workflow)

    comfyui_check = subparsers.add_parser("comfyui-check", help="Check whether a ComfyUI HTTP API server is reachable")
    comfyui_check.add_argument("--url", default="http://127.0.0.1:8188")
    comfyui_check.set_defaults(func=cmd_comfyui_check)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "generate" and not args.config and not args.fan_refs:
        parser.error("generate requires --fan-refs unless --config is provided")
    if args.command == "generate" and not args.config and args.output is None:
        args.output = "outputs/result.svg"
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

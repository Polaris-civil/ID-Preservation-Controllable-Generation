"""Run an offline end-to-end demo.

The script uses placeholder reference paths and writes a deterministic SVG plus
a JSON manifest. It proves that the package, CLI contracts, and workflow glue
are usable before downloading real model weights.
"""

from id_preservation_cg import ControllableGenerationPipeline, GenerationRequest
from id_preservation_cg.config import ControlConfig


def main() -> None:
    request = GenerationRequest(
        fan_refs=["examples/assets/fan_01.jpg", "examples/assets/fan_02.jpg"],
        celebrity_refs=["examples/assets/star_01.jpg"],
        pose_image="examples/assets/openpose.png",
        prompt="a fan and a famous singer taking a friendly red-carpet photo",
        clothing_prompt="fan wearing a silver jacket, celebrity wearing a black stage suit",
        scene_prompt="cinematic red carpet, warm flash photography",
        output_path="outputs/demo_result.svg",
        controls=ControlConfig(use_lora=True, use_ip_adapter=True, use_controlnet=True, use_style_lora=True),
    )
    result = ControllableGenerationPipeline().generate(request)
    print(result)


if __name__ == "__main__":
    main()

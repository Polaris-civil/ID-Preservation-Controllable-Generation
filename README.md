# ID-Preservation Controllable Generation

A modular text-to-image scaffold for identity-preserving and controllable
two-person photo generation. The target workflow is a fan-celebrity photo where
the fan identity remains stable while pose, outfit, and scene can be controlled
independently.

The repository is designed as a complete GitHub project, not a single script. It
ships with an offline mock backend, CLI, Python API, LoRA training manifest
builder, ComfyUI workflow template, tests, CI, and production integration notes.

## Why This Project Exists

Few-shot identity tuning often overfits to the clothes, pose, camera angle, or
background in the reference images. Prompt-only generation gives more creative
control, but identity consistency usually drops. This project separates the
problem into four semantic slots:

- ID: stable person-specific features.
- Pose: action, body layout, camera view.
- Clothing: outfit and accessories.
- Background: location, lighting, scene style.

The generation workflow then combines LoRA, IP-Adapter, ControlNet, and optional
Style LoRA or Redux-like control.

## Core Features

| Area | Capability | Default implementation | Production path |
| --- | --- | --- | --- |
| Tagging | Extract image tags in a WD14-like interface | deterministic offline tagger | WD14 ONNX or Transformers model |
| Semantic reconstruction | Convert raw tags into ID, pose, clothing, background | rule-based VLM simulator | Qwen-VL, DeepSeek-VL, or another VLM |
| Few-shot ID learning | Prepare LoRA captions from 5-20 images | manifest and placeholder adapter | Diffusers/Accelerate LoRA training |
| Regularization | Prompt Dropout and tag perturbation | built into dataset builder | reuse in the real dataloader |
| Face consistency | IP-Adapter control layer | manifest controller | ComfyUI IP-Adapter extension |
| Pose control | OpenPose-style ControlNet control | manifest controller | SDXL/HunyuanDiT ControlNet |
| Style transfer | Outfit/background style control | switchable controller | Style LoRA, Redux, reference-only |
| Backends | Offline and ComfyUI-ready generation | SVG preview and API payload writer | ComfyUI submit or native Diffusers backend |

## Architecture

```text
Reference images
      |
      v
WD14-like tagger
      |
      v
VLM semantic reconstructor
      |
      +--> ID tags ---------> few-shot LoRA captions/training
      +--> Pose tags -------> ControlNet/OpenPose conditioning
      +--> Clothing tags ---> Style LoRA or Redux prompt channel
      +--> Background ------> scene prompt channel

GenerationRequest
      |
      v
Controller stack: LoRA + IP-Adapter + ControlNet + Style
      |
      v
Backend: mock SVG, ComfyUI API payload, or custom Diffusers backend
```

## Quick Start

```bash
cd ID-Preservation-Controllable-Generation
python -m pip install -e .
python examples/run_demo.py
```

Python 3.9 or newer is required.

The demo writes:

```text
outputs/demo_result.svg
outputs/demo_result.manifest.json
```

The demo uses placeholder file paths. The offline tagger is deterministic and
does not require real images, so the project can be tested immediately.

## CLI Usage

Extract and decouple tags:

```bash
idpcg tag examples/assets/fan_01.jpg examples/assets/fan_02.jpg --role fan
```

Prepare a few-shot LoRA manifest:

```bash
idpcg train-lora examples/assets/fan_01.jpg examples/assets/fan_02.jpg \
  --trigger-token fan_person \
  --rank 16 \
  --alpha 16 \
  --prompt-dropout 0.15 \
  --tag-noise 0.1 \
  --output-dir checkpoints/fan_lora
```

Generate with direct CLI arguments:

```bash
idpcg generate \
  --fan-refs examples/assets/fan_01.jpg examples/assets/fan_02.jpg \
  --celebrity-refs examples/assets/star_01.jpg \
  --pose-image examples/assets/openpose.png \
  --prompt "a fan and a famous singer taking a friendly red-carpet photo" \
  --clothing-prompt "fan wearing a silver jacket, celebrity wearing a black stage suit" \
  --scene-prompt "cinematic red carpet, warm flash photography" \
  --use-style-lora \
  --output outputs/result.svg
```

Generate from a config file:

```bash
idpcg generate --config examples/generation_request.json
```

Create a ComfyUI payload without submitting a job:

```bash
idpcg generate --config examples/comfyui_request.json
```

Copy the bundled ComfyUI workflow template:

```bash
idpcg workflow --output outputs/comfyui_workflow.json
```

## Python API

```python
from id_preservation_cg import ControllableGenerationPipeline, GenerationRequest
from id_preservation_cg.config import ControlConfig

request = GenerationRequest(
    fan_refs=["fan_01.jpg", "fan_02.jpg"],
    celebrity_refs=["star_01.jpg"],
    pose_image="openpose.png",
    prompt="a fan and a celebrity taking a realistic photo together",
    clothing_prompt="matching concert outfits",
    scene_prompt="night concert stage",
    controls=ControlConfig(use_lora=True, use_ip_adapter=True, use_controlnet=True),
)

result = ControllableGenerationPipeline().generate(request)
print(result["image"], result["manifest"])
```

## Repository Layout

```text
src/id_preservation_cg/
  backends.py       backend adapters: mock SVG and ComfyUI payload writer
  cli.py            command line interface
  config.py         dataclass configs and config file loading
  controllers.py    IP-Adapter, ControlNet, Style controller abstractions
  dataset.py        caption building, prompt dropout, tag perturbation
  lora.py           few-shot LoRA training facade
  pipeline.py       end-to-end orchestration
  semantic.py       VLM-style tag reconstruction and decoupling
  tagging.py        WD14-like tagger facade
examples/           runnable demos and request configs
workflows/          ComfyUI workflow template
docs/               production backend and safety notes
tests/              offline tests
```

## Real Model Integration

Install optional model dependencies only when needed:

```bash
pip install -r requirements-full.txt
```

Then replace the mock parts in this order:

1. Implement a real WD14-compatible tagger in `tagging.py`.
2. Replace the rule-based reconstructor in `semantic.py` with Qwen-VL,
   DeepSeek-VL, or another VLM that returns the fixed JSON slot schema.
3. Implement `LoraTrainer._run_real_training` with Diffusers/Accelerate.
4. Use `model.backend = "comfyui"` to write or submit ComfyUI jobs, or add a
   native Diffusers backend in `backends.py`.

See [docs/REAL_BACKEND.md](docs/REAL_BACKEND.md) for details.

## Testing

```bash
python -m pip install -e .
python -m unittest discover -s tests
python examples/run_demo.py
idpcg generate --config examples/generation_request.json
```

## Safety

Use only reference images you have the right to use. Real deployments should add
consent tracking, watermarking, audit logs, and abuse prevention. See
[docs/SAFETY.md](docs/SAFETY.md).

## Acknowledgements

This project follows common workflow ideas from WD14 Tagger, LoRA, IP-Adapter,
ControlNet, ComfyUI, SDXL, and HunyuanDiT ecosystems.

## License

Apache-2.0. See [LICENSE](LICENSE).

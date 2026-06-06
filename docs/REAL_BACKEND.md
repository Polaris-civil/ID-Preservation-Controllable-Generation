# Real Backend Integration

The repository defaults to `backend=mock` so CI and local smoke tests do not
download large models. Production deployments should replace three seams.

## 1. Tagger

Implement `WD14LikeTagger.extract` with a real WD14-compatible model:

```python
class WD14LikeTagger:
    def __init__(self, model_path: str, threshold: float = 0.35):
        ...

    def extract(self, image_path):
        # load image, resize, normalize
        # run model
        # keep tags above threshold
        return ImageTags(path=str(image_path), tags=tags, confidence=mean_score)
```

Keep the return contract stable so `semantic.py` and `dataset.py` continue to
work.

## 2. VLM Semantic Reconstruction

Replace the rule-based reconstructor with a Qwen-VL or DeepSeek-VL call that
returns this schema:

```json
{
  "identity": ["face shape", "eye detail", "hair style"],
  "pose": ["standing", "three-quarter view"],
  "clothing": ["silver jacket"],
  "background": ["red carpet", "flash photography"]
}
```

The important constraint is that identity tokens must not include fixed clothing
or fixed background details.

## 3. Image Generation Backend

Use `ModelConfig.backend = "comfyui"` to write a ComfyUI API payload:

```bash
idpcg generate --config examples/comfyui_request.json
```

Set `submit_comfyui_job` to `true` only after confirming your local workflow
node names match `workflows/comfyui_workflow.json`.

For native Diffusers inference, add a backend class beside `ComfyUIBackend` and
register it in `backend_for_request`.

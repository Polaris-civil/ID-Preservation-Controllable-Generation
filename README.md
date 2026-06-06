# ID-Preservation Controllable Generation

一个面向“人物 ID 保持 + 可控生成”的文生图项目骨架，目标场景是生成粉丝与明星的高一致性合照：粉丝身份特征稳定，明星脸部结构一致，同时支持控制动作、服装和场景。

本仓库不是单个脚本，而是一个完整可安装的 Python 项目。它包含离线 mock 后端、命令行工具、Python API、LoRA 训练清单生成器、ComfyUI 工作流模板、测试、CI，以及真实模型接入说明。

默认实现不下载大模型，方便先跑通完整流程。真实生成时可以把 mock 后端替换为 ComfyUI、SDXL、HunyuanDiT 或 Diffusers 后端。

## 项目痛点

少样本人像 LoRA 微调时，很容易把人物 ID、衣服、姿态、背景绑定在一起学习。例如参考图里一直是同一件衣服、同一角度、同一背景，模型就可能把这些非身份信息也记进 ID。这样生成时虽然人像像，但动作和场景泛化差。

本项目采用语义解耦思路，将图像标签拆成四类：

- ID：脸型、五官、发型、肤色等身份特征。
- 姿态：动作、视角、身体布局、站姿或坐姿。
- 服装：衣服、配饰、材质、穿搭风格。
- 背景：地点、光照、场景风格、摄影环境。

生成阶段再通过 LoRA、IP-Adapter、ControlNet、Style LoRA 或 Redux 风格模块协同控制。

## 核心特性

| 模块 | 能力 | 当前实现 | 真实模型替换建议 |
| --- | --- | --- | --- |
| 图像标签提取 | 从参考图自动提取视觉标签 | WD14-like 离线模拟 Tagger | WD14 ONNX 或 Transformers Tagger |
| 多模态语义重构 | 将原始标签重构为 ID、姿态、服装、背景 | 规则化 VLM 模拟器 | Qwen-VL、DeepSeek-VL 或其他 VLM |
| 小样本 LoRA | 5-20 张图学习人物 ID | 生成训练 manifest 和占位 adapter | Diffusers / Accelerate LoRA 训练 |
| 防过拟合策略 | Prompt Dropout、标签扰动 | 已内置在 dataset builder | 接入真实 dataloader |
| 人脸一致性 | 约束人脸结构与身份一致 | IP-Adapter 控制器 manifest | ComfyUI IP-Adapter 插件 |
| 动作控制 | 使用 OpenPose 等姿态图控制动作 | ControlNet 控制器 manifest | SDXL / HunyuanDiT ControlNet |
| 风格迁移 | 控制服装、背景和整体风格 | Style Controller 开关 | Style LoRA、Redux、Reference-only |
| 后端 | 离线预览、ComfyUI payload | mock SVG、ComfyUI payload writer | ComfyUI 提交或原生 Diffusers 后端 |

## 系统架构

```text
参考图像
  |
  v
WD14-like Tagger
  |
  v
多模态语义重构器
  |
  +--> ID 标签 ---------> 少样本 LoRA 训练
  +--> 姿态标签 --------> ControlNet / OpenPose 控制
  +--> 服装标签 --------> Style LoRA / Redux / prompt 控制
  +--> 背景标签 --------> 场景 prompt / 风格控制

GenerationRequest
  |
  v
控制器栈：LoRA + IP-Adapter + ControlNet + Style
  |
  v
生成后端：mock SVG / ComfyUI API payload / 自定义 Diffusers 后端
```

## 安装

进入项目目录：

```bash
cd ID-Preservation-Controllable-Generation
```

安装为可编辑包：

```bash
python -m pip install -e .
```

Python 版本要求：

```text
Python >= 3.9
```

如果后续要接入真实 SDXL、HunyuanDiT、Diffusers 或 ControlNet 训练推理，再安装完整依赖：

```bash
pip install -r requirements-full.txt
```

## 快速运行

运行离线 demo：

```bash
python examples/run_demo.py
```

输出文件：

```text
outputs/demo_result.svg
outputs/demo_result.manifest.json
```

说明：

- `demo_result.svg` 是离线 mock 后端生成的可视化占位结果。
- `demo_result.manifest.json` 记录完整请求、prompt、解耦标签、控制器配置和后端信息。
- 默认不需要真实图片；示例路径即使不存在，也可以跑通流程。

## 命令行使用

### 1. 提取并解耦标签

```bash
idpcg tag examples/assets/fan_01.jpg examples/assets/fan_02.jpg --role fan
```

输出会包含两部分：

- `raw`：模拟 WD14 Tagger 提取的原始标签。
- `decoupled`：拆分后的 ID、姿态、服装、背景标签。

### 2. 准备 LoRA 训练清单

```bash
idpcg train-lora examples/assets/fan_01.jpg examples/assets/fan_02.jpg \
  --trigger-token fan_person \
  --rank 16 \
  --alpha 16 \
  --prompt-dropout 0.15 \
  --tag-noise 0.1 \
  --output-dir checkpoints/fan_lora
```

输出：

```text
checkpoints/fan_lora/training_manifest.json
checkpoints/fan_lora/adapter_model.safetensors
```

当前 `adapter_model.safetensors` 是占位文件，用于表达完整流程。真实训练需要在 `LoraTrainer._run_real_training` 中接入 Diffusers 或 Accelerate。

### 3. 直接用 CLI 生成合照

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

输出：

```text
outputs/result.svg
outputs/result.manifest.json
```

### 4. 用配置文件生成

推荐使用配置文件管理复杂参数：

```bash
idpcg generate --config examples/generation_request.json
```

配置示例在：

```text
examples/generation_request.json
```

它包含：

- 粉丝参考图路径。
- 明星参考图路径。
- OpenPose 姿态图路径。
- 正向 prompt 和反向 prompt。
- 服装、场景 prompt。
- LoRA、IP-Adapter、ControlNet、Style LoRA 开关。
- 后端配置。

### 5. 生成 ComfyUI payload

如果你要接入 ComfyUI，可以先生成真正的 ComfyUI API payload，而不提交任务：

```bash
idpcg generate --config examples/comfyui_request.json
```

输出类似：

```text
outputs/comfyui_result.manifest.json
outputs/comfyui_result.comfyui_payload.json
```

`outputs/comfyui_result.comfyui_payload.json` 是可提交给 ComfyUI `/prompt` 接口的 API graph，不是说明型占位 JSON。

默认 `submit_comfyui_job` 是 `false`。确认本地 ComfyUI 已启动，且 checkpoint 名称存在后，再在配置里改为：

先检查 ComfyUI 服务是否在线：

```bash
idpcg comfyui-check --url http://127.0.0.1:8188
```

```json
"submit_comfyui_job": true
```

然后运行：

```bash
idpcg generate --config examples/comfyui_request.json
```

后端会执行：

1. 读取或生成 ComfyUI API workflow。
2. 将 prompt、negative prompt、seed、checkpoint 等参数填入节点。
3. 如果本地参考图存在，上传到 `/upload/image`。
4. 提交到 `/prompt`。
5. 轮询 `/history/{prompt_id}`。
6. 通过 `/view` 下载第一张输出图到 `output_path`。

内置的可运行基础工作流是：

```text
workflows/comfyui_api_txt2img.json
```

这个工作流只依赖 ComfyUI 原生节点：

- `CheckpointLoaderSimple`
- `CLIPTextEncode`
- `EmptyLatentImage`
- `KSampler`
- `VAEDecode`
- `SaveImage`

如果你要启用 IP-Adapter、ControlNet、LoRA 等扩展节点，需要从 ComfyUI 导出 API 格式 workflow，然后在 `examples/comfyui_request.json` 中把 `comfyui_workflow` 指向你的自定义 JSON。自定义 workflow 可以使用这些占位符：

```text
{{checkpoint}}
{{positive_prompt}}
{{negative_prompt}}
{{seed}}
{{width}}
{{height}}
{{batch_size}}
{{steps}}
{{cfg}}
{{sampler_name}}
{{scheduler}}
{{filename_prefix}}
{{pose_image_upload}}
{{fan_ref_upload}}
{{celebrity_ref_upload}}
```

### 6. 导出 ComfyUI 工作流模板

```bash
idpcg workflow --output outputs/comfyui_workflow.json
```

这个命令默认导出说明型可视化模板。要导出可直接提交 `/prompt` 的 API workflow：

```bash
idpcg workflow --kind api --output outputs/comfyui_api_txt2img.json
```

模板源文件：

```text
workflows/comfyui_workflow.json
workflows/comfyui_api_txt2img.json
```

安装包内也包含同一份模板：

```text
src/id_preservation_cg/assets/comfyui_workflow.json
```

## Python API 使用

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
    controls=ControlConfig(
        use_lora=True,
        use_ip_adapter=True,
        use_controlnet=True,
        use_style_lora=True,
    ),
)

result = ControllableGenerationPipeline().generate(request)
print(result["image"])
print(result["manifest"])
```

## 目录结构

```text
src/id_preservation_cg/
  backends.py       生成后端：mock SVG、ComfyUI payload
  cli.py            命令行入口
  config.py         配置 dataclass、JSON/YAML 加载
  controllers.py    IP-Adapter、ControlNet、Style 控制器抽象
  dataset.py        caption 构建、Prompt Dropout、标签扰动
  lora.py           LoRA 小样本训练门面
  pipeline.py       端到端生成编排
  semantic.py       多模态语义重构与四类标签解耦
  tagging.py        WD14-like Tagger 接口
  validation.py     输入配置校验

examples/
  run_demo.py
  generation_request.json
  comfyui_request.json

workflows/
  comfyui_workflow.json

docs/
  REAL_BACKEND.md
  SAFETY.md

tests/
  test_*.py
```

## 接入真实模型的建议路径

### 1. 替换真实 WD14 Tagger

修改：

```text
src/id_preservation_cg/tagging.py
```

保持返回类型不变：

```python
ImageTags(path=str(image_path), tags=tags, confidence=score)
```

### 2. 接入 Qwen-VL 或 DeepSeek-VL

修改：

```text
src/id_preservation_cg/semantic.py
```

要求 VLM 输出固定 schema：

```json
{
  "identity": ["face shape", "eye detail", "hair style"],
  "pose": ["standing", "three-quarter view"],
  "clothing": ["silver jacket"],
  "background": ["red carpet", "flash photography"]
}
```

关键原则：ID 标签里不要混入衣服和背景，否则 LoRA 容易过拟合。

### 3. 接入真实 LoRA 训练

修改：

```text
src/id_preservation_cg/lora.py
```

重点实现：

```python
LoraTrainer._run_real_training(...)
```

建议使用：

- SDXL 或 HunyuanDiT 作为 base model。
- LoRA rank/alpha 控制容量。
- Prompt Dropout 降低姿态和服装绑定。
- 标签扰动增强泛化。

### 4. 接入 ComfyUI 或 Diffusers 生成

ComfyUI 已有 payload 后端：

```text
src/id_preservation_cg/backends.py
```

如果要接入原生 Diffusers，可以新增一个后端类，例如：

```python
class DiffusersBackend:
    def render(...):
        ...
```

然后在：

```python
backend_for_request(...)
```

里注册。

## 测试

运行标准库测试：

```bash
python -m unittest discover -s tests
```

运行基础 smoke test：

```bash
python examples/run_demo.py
idpcg generate --config examples/generation_request.json
idpcg generate --config examples/comfyui_request.json
```

## 注意事项

真实人像生成属于敏感能力。正式使用前建议加入：

- 参考图授权和同意记录。
- 生成图水印或 AI 标识。
- prompt、seed、adapter、输出 hash 审计日志。
- 防冒充、防骚扰、防侵权、防虚假信息策略。
- 对真人、公众人物和未成年人内容的额外限制。

更多说明见：

```text
docs/SAFETY.md
docs/REAL_BACKEND.md
```

## 许可证

Apache-2.0。详见：

```text
LICENSE
```

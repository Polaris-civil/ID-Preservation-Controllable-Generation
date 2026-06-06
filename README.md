# ID-Preservation Controllable Generation

[![CI](https://github.com/CodexTesla/ID-Preservation-Controllable-Generation/actions/workflows/ci.yml/badge.svg)](https://github.com/CodexTesla/ID-Preservation-Controllable-Generation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.9_%7C_3.10_%7C_3.12-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![uv](https://img.shields.io/badge/build-uv-724d97?logo=astral)](https://docs.astral.sh/uv/)

一个面向”人物 ID 保持 + 可控生成”的文生图项目骨架，目标场景是生成粉丝与明星的高一致性合照：粉丝身份特征稳定，明星脸部结构一致，同时支持控制动作、服装和场景。

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
uv sync --extra dev
```

Python 版本要求：

```text
Python >= 3.9
```

如果后续要接入真实 SDXL、HunyuanDiT、Diffusers 或 ControlNet 训练推理，再安装完整依赖：

```bash
uv sync --extra full
```

## 快速运行

运行离线 demo：

```bash
uv run python examples/run_demo.py
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

## 本机 ComfyUI 启动方式

如果 ComfyUI 安装在本仓库同级目录：

```text
E:\trae\AIGC_github\ComfyUI
```

可以在本项目目录中启动：

```powershell
.\scripts\start_comfyui.ps1
```

停止：

```powershell
.\scripts\stop_comfyui.ps1
```

浏览器打开：

```text
http://127.0.0.1:8188
```

检查 API：

```bash
uv run idpcg comfyui-check --url http://127.0.0.1:8188
```

## 命令行使用

### 1. 提取并解耦标签

```bash
uv run idpcg tag examples/assets/fan_01.jpg examples/assets/fan_02.jpg --role fan
```

输出会包含两部分：

- `raw`：模拟 WD14 Tagger 提取的原始标签。
- `decoupled`：拆分后的 ID、姿态、服装、背景标签。

### 2. 准备 LoRA 训练清单

```bash
uv run idpcg train-lora examples/assets/fan_01.jpg examples/assets/fan_02.jpg \
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
uv run idpcg generate \
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

推荐使用 **YAML** 格式的配置文件（支持注释，易读易改）。项目也兼容 JSON 格式。

```bash
# YAML 格式（推荐 — 有注释，可读性好）
uv run idpcg generate --config examples/generation_request.yaml

# JSON 格式（也支持）
uv run idpcg generate --config examples/generation_request.yaml
```

配置文件包含以下内容：

- 粉丝参考图路径。
- 明星参考图路径。
- OpenPose 姿态图路径。
- 正向 prompt 和反向 prompt。
- 服装、场景 prompt。
- LoRA、IP-Adapter、ControlNet、Style LoRA 开关。
- 后端配置。

> **小提示：** `examples/` 里的 `.yaml` 是**项目配置文件**（CLI 读取），`workflows/` 里的 `.json` 是 **ComfyUI 工作流**（ComfyUI 读取）。用后缀就能一眼区分，不会搞混。

### 5. 生成 ComfyUI payload

如果你要接入 ComfyUI，可以先生成真正的 ComfyUI API payload，而不提交任务：

```bash
uv run idpcg generate --config examples/comfyui_request.yaml
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
uv run idpcg comfyui-check --url http://127.0.0.1:8188
```

```json
"submit_comfyui_job": true
```

对于你当前电脑上的 RTX 4060 8GB，建议先用 SD1.5 512x512：

```json
"base_model": "v1-5-pruned-emaonly.safetensors",
"width": 512,
"height": 512,
"steps": 25,
"cfg": 7.0
```

然后运行：

```bash
uv run idpcg generate --config examples/comfyui_request.yaml
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

如果你要启用 IP-Adapter、ControlNet、LoRA 等扩展节点，需要从 ComfyUI 导出 API 格式 workflow，然后在 `examples/comfyui_request.yaml` 中把 `comfyui_workflow` 指向你的自定义 JSON。自定义 workflow 可以使用这些占位符：

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
uv run idpcg workflow --output outputs/comfyui_workflow.json
```

这个命令默认导出说明型可视化模板。要导出可直接提交 `/prompt` 的 API workflow：

```bash
uv run idpcg workflow --kind api --output outputs/comfyui_api_txt2img.json
```

要导出 LoRA + OpenPose ControlNet 的现成模块组合 workflow：

```bash
uv run idpcg workflow --kind lora-openpose --output outputs/comfyui_api_lora_openpose.json
```

模板源文件：

```text
workflows/comfyui_workflow.json
workflows/comfyui_api_txt2img.json
workflows/comfyui_api_lora_openpose.json
```

安装包内也包含同一份模板：

```text
src/id_preservation_cg/assets/comfyui_workflow.json
```

## 免训练现成模块流程

如果暂时不训练自己的 ID LoRA，可以先用现成模块验证完整链路。本项目提供了一个示例配置：

```text
examples/comfyui_lora_openpose_request.yaml
```

它使用：

```text
基础模型: v1-5-pruned-emaonly.safetensors
LoRA: lcm-lora-sdv1-5.safetensors
ControlNet: control_v11p_sd15_openpose.safetensors
姿态图: examples/assets/openpose_two_person.png
Workflow: workflows/comfyui_api_lora_openpose.json
```

运行：

```bash
uv run idpcg generate --config examples/comfyui_lora_openpose_request.yaml
```

输出：

```text
outputs/comfyui_lora_openpose.png
outputs/comfyui_lora_openpose.manifest.json
outputs/comfyui_lora_openpose.comfyui_payload.json
outputs/comfyui_lora_openpose.comfyui_history.json
```

这一步的意义是验证：

- 本项目可以组织 prompt 和控制器信息。
- ComfyUI 可以加载现成 LoRA。
- ComfyUI 可以加载现成 OpenPose ControlNet。
- 姿态图可以通过 API 上传并接入 LoadImage。
- 生成结果和完整记录可以保存下来。

注意：这里的 LCM LoRA 是加速/采样风格 LoRA，不是人物身份 LoRA。后续把它替换成你自己训练的身份 LoRA，才是本项目真正的核心价值。

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

### 整体概览

```text
ID-Preservation-Controllable-Generation/
├── src/id_preservation_cg/    ← 🧠 核心代码（Python 包）
├── examples/                  ← 📋 示例配置文件 + 示例脚本 + 示例素材
├── workflows/                 ← 🔧 ComfyUI 工作流模板（可拖进 ComfyUI）
├── outputs/                   ← 🖼️ 生成结果输出
├── scripts/                   ← ⚡ PowerShell 辅助脚本
├── tests/                     ← 🧪 单元测试
├── docs/                      ← 📖 补充文档
├── pyproject.toml             ← 📦 项目元信息与依赖声明
└── README.md                  ← 📄 你正在读的文件
```

### 🧠 `src/id_preservation_cg/` — 核心大脑

整个项目的 Python 包。每一个模块各司其职：

| 文件 | 一句话 | 管什么 |
|------|--------|--------|
| `tagging.py` | **图像打标器** | 从照片里提取原始标签（黑头发、圆脸、站姿、红背景…）。目前是模拟版，可替换为真实 WD14 模型 |
| `semantic.py` | **语义解耦器** | 把原始标签拆成四类：**身份 / 姿态 / 服装 / 背景**。这就是项目的核心创意——不让它们混在一起学 |
| `lora.py` | **LoRA 训练门面** | 管理身份 LoRA 的小样本训练流程。目前生成占位模型文件，真训练时接入 Diffusers 或 Accelerate |
| `dataset.py` | **数据集构建** | LoRA 训练时构建 caption 数据集，内置 Prompt Dropout 和标签扰动来防过拟合 |
| `controllers.py` | **控制器栈** | 三个可独立开关的控制器：IP-Adapter（锁脸）、ControlNet（控姿势）、Style（控风格），每个都能调强度 |
| `config.py` | **配置中心** | 所有参数的数据结构（`GenerationRequest`、`ModelConfig`、`ControlConfig`）。JSON 配置文件最终反序列化到这里 |
| `pipeline.py` | **总流程编排** | 把打标 → 解耦 → 加载控制器 → 后端生成串成一条端到端流水线 |
| `backends.py` | **生成后端** | 两种模式：Mock 后端生成占位 SVG 图；ComfyUI 后端提交 API 任务真出图，支持上传参考图、轮询结果、下载输出 |
| `cli.py` | **命令行入口** | `idpcg tag`、`idpcg generate`、`idpcg train-lora`、`idpcg workflow` 等命令都在这里定义 |
| `validation.py` | **输入校验** | 检查请求参数是否合法（路径、开关冲突、数值范围等） |
| `assets/` | **内置资源** | 随包分发的工作流模板副本，与 `workflows/` 目录内容同步 |

### 📋 `examples/` — 示例配置与素材

> **注意：`examples/` 里的文件和 `workflows/` 里的文件是两种完全不同的东西！**
>
> | | `examples/*.yaml` / `examples/*.json` | `workflows/*.json` |
> |---|---|---|
> | **是什么** | 📋 项目配置文件（YAML 或 JSON） | 🔧 ComfyUI 工作流（ComfyUI 原生 API 格式） |
> | **能拖进 ComfyUI 吗** | ❌ 不能，ComfyUI 不认识 | ✅ 能，直接拖就显示节点图 |
> | **内容是什么** | 用哪张照片、写什么提示词、开哪些控制器 | 节点怎么连：Checkpoint→LoRA→ControlNet→KSampler→VAE |
> | **谁来读** | 项目的 CLI（`idpcg generate --config xxx.yaml`） | ComfyUI 画布 / ComfyUI API |
>
> 一句话：**配置文件告诉项目"画什么"，工作流告诉 ComfyUI"怎么画"。**
>
> **推荐用 `.yaml` 格式**作为配置文件——支持注释，层级靠缩进一目了然。后缀就能区分：`.yaml` = 项目配置，`.json` = ComfyUI 工作流。

| 文件 | 干什么 |
|------|--------|
| `run_demo.py` | 一键 Demo 脚本，跑通完整 mock 流程 |
| `generation_request.yaml` | Mock 模式配置——后端 `mock`，生成占位 SVG 快速验证 |
| `comfyui_request.yaml` | ComfyUI 基础配置——txt2img 工作流 |
| `comfyui_lora_openpose_request.yaml` | LoRA + ControlNet 组合——免训练验证多控制器链路 |
| `comfyui_full_pipeline_request.yaml` | 🆕 完全体——LoRA + IP-Adapter + ControlNet 三合一 |
| `assets/` 子目录 | 示例素材图片（fan_01.jpg、star_01.jpg、openpose.png 等） |

### 🔧 `workflows/` — ComfyUI 工作流模板

每个 JSON 文件描述一个 ComfyUI 画布上的节点图。可以直接拖进 ComfyUI 界面查看和编辑。

| 文件 | 复杂度 | 包含的节点 |
|------|--------|-----------|
| `comfyui_workflow.json` | ⭐ | 可视化模板，给人看的参考图，不可提交 API |
| `comfyui_api_txt2img.json` | ⭐⭐ | 最简文生图：加载模型 → 写 prompt → 出图（仅 ComfyUI 原生节点） |
| `comfyui_api_lora_openpose.json` | ⭐⭐⭐ | LoRA + ControlNet：模型加载 → LoRA 注入 → 骨骼图控姿势 → 出图 |
| `comfyui_api_full_pipeline.json` | ⭐⭐⭐⭐⭐ | 🆕 全家桶：LoRA + IP-Adapter（锁脸）+ ControlNet（控姿势）→ 出图 |

层级演进关系：

```text
comfyui_api_txt2img.json          ← 地基（就一个文生图）
        ↓ 加 LoRA + ControlNet
comfyui_api_lora_openpose.json    ← 进阶（能控姿势了）
        ↓ 再加 IP-Adapter
comfyui_api_full_pipeline.json    ← 完全体（脸也锁住了）
```

工作流使用 ComfyUI API 格式，节点中使用 `{{placeholder}}` 占位符。运行 `idpcg generate` 时，后端会自动将占位符替换为配置中的实际值（prompt、seed、checkpoint 名称、上传后的图片路径等）。

### 🖼️ `outputs/` — 输出目录

每次运行生成任务，产物都放在这里：

| 后缀 | 是什么 |
|------|--------|
| `.svg` | Mock 模式生成的占位示意图（不是真照片，仅用于验证流程） |
| `.png` | ComfyUI 真出图的实际图片 |
| `.manifest.json` | **运行全记录**：输入参数、解耦后的标签、使用的控制器、后端信息、输出路径 |
| `.comfyui_payload.json` | 发送给 ComfyUI `/prompt` 接口的完整请求体（可审计、可复现） |
| `.comfyui_response.json` | ComfyUI 返回的原始响应（含 prompt_id） |
| `.comfyui_history.json` | ComfyUI 生成完成后的历史记录（含输出文件名，用于下载图片） |

### ⚡ `scripts/` — PowerShell 辅助脚本

| 脚本 | 一句话 |
|------|--------|
| `start_comfyui.ps1` | 启动本仓库同级目录下的 ComfyUI（自动定位 `../ComfyUI/main.py`） |
| `stop_comfyui.ps1` | 关闭 ComfyUI 后台进程 |
| `create_demo_refs.ps1` | 创建演示用的参考图素材 |

### 🧪 其余目录

| 目录 | 内容 |
|------|------|
| `tests/` | 单元测试，运行 `uv run python -m unittest discover -s tests` 执行（目前 11 个测试） |
| `docs/` | 补充文档：《接入真实模型指南》《安全注意事项》《ComfyUI 新手教程》 |
| `pyproject.toml` | Python 项目的"身份证"：名称、版本、依赖声明、CLI 入口点 |

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
uv run python -m unittest discover -s tests
```

运行基础 smoke test：

```bash
uv run python examples/run_demo.py
uv run idpcg generate --config examples/generation_request.yaml
uv run idpcg generate --config examples/comfyui_request.yaml
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
docs/COMFYUI_BEGINNER_GUIDE.md
docs/SAFETY.md
docs/REAL_BACKEND.md
```

## 许可证

Apache-2.0。详见：

```text
LICENSE
```

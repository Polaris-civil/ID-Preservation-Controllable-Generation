# ID-Preservation Controllable Generation

[![CI](https://github.com/Polaris-civil/ID-Preservation-Controllable-Generation/actions/workflows/ci.yml/badge.svg)](https://github.com/Polaris-civil/ID-Preservation-Controllable-Generation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.9_%7C_3.10_%7C_3.12-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![uv](https://img.shields.io/badge/build-uv-724d97?logo=astral)](https://docs.astral.sh/uv/)

### 简体中文

只需准备少量人物参考图、姿态图和文本提示词，就可以组织一条“人物 ID 保持 + 姿态控制 + 服装场景控制”的文生图生成链路。

本项目不是单个出图脚本，而是一个可安装、可测试、可替换真实模型的 Python 工程骨架。默认使用离线 mock 后端，不下载大模型，也能先跑通完整流程；需要真实出图时，可以切换到 ComfyUI，并逐步接入 LoRA、IP-Adapter、ControlNet、SDXL、HunyuanDiT 或 Diffusers。

## 功能特性

- [x] 支持人物参考图标签提取，并将标签拆分为 `身份`、`姿态`、`服装`、`背景` 四类。
- [x] 支持少样本身份 LoRA 训练清单生成，内置 Prompt Dropout 和标签扰动策略。
- [x] 支持 IP-Adapter、ControlNet、Style LoRA 等控制器配置，便于组合身份、动作和风格控制。
- [x] 支持离线 mock 后端，适合无显卡、无模型环境下验证 pipeline、CLI 和测试。
- [x] 支持 ComfyUI API payload 生成，并可选择提交任务、轮询历史、下载输出图片。
- [x] 提供基础 txt2img、LoRA + OpenPose、完整多控制器 ComfyUI 工作流模板。
- [x] 提供命令行工具 `idpcg`，支持打标、生成、LoRA 清单、工作流导出和 ComfyUI 连通性检查。
- [x] 提供 Python API，可以在自己的脚本或服务中直接调用生成流水线。
- [x] 包含单元测试、CI、真实模型接入说明和安全注意事项。

## 适用场景

- 生成粉丝与明星、角色与角色、用户与虚拟形象的合照实验。
- 研究少样本人像 LoRA 中“身份特征”和“服装、姿态、背景”绑定过强的问题。
- 将 ComfyUI 工作流纳入可复现的 Python 工程，而不是只在画布里手动调节点。
- 为后续接入真实 WD14 Tagger、VLM、Diffusers 或训练框架提供工程起点。

## 配置要求

- Python `>= 3.9`
- 推荐使用 [uv](https://docs.astral.sh/uv/) 管理环境和依赖。
- mock 模式不需要 GPU，也不需要下载模型。
- ComfyUI 真出图需要本机已安装 ComfyUI，并准备对应 checkpoint、LoRA、ControlNet 或 IP-Adapter 模型。

| 项目 | 最低配置 | 推荐配置 | 说明 |
| ---- | -------- | -------- | ---- |
| CPU | 4 核 | 6 核及以上 | mock、配置生成、payload 生成主要依赖 CPU |
| RAM | 4 GB | 8 GB 及以上 | ComfyUI 和本地模型越多，内存需求越高 |
| GPU | 非必须 | 6 GB 显存及以上 | 真实出图和训练建议使用独立显卡 |
| 磁盘 | 1 GB | 20 GB 及以上 | mock 项目很小，真实模型会占用大量空间 |

## 快速开始

### 推荐使用方式

- 只想先看流程：运行 `examples/run_demo.py`，不需要模型。
- 想验证 CLI 和配置文件：运行 `idpcg generate --config examples/generation_request.yaml`。
- 想接入真实出图：先启动 ComfyUI，再运行 `examples/comfyui_request.yaml`。
- 想做身份一致性实验：先准备人物参考图，生成 LoRA 训练 manifest，再替换真实训练逻辑。

### 1. 安装依赖

```bash
git clone https://github.com/Polaris-civil/ID-Preservation-Controllable-Generation.git
cd ID-Preservation-Controllable-Generation
uv sync --extra dev
```

如果后续要接入 Diffusers、Transformers、训练或图像处理依赖，再安装完整依赖：

```bash
uv sync --extra full
```

### 2. 运行离线 Demo

```bash
uv run python examples/run_demo.py
```

输出文件：

```text
outputs/demo_result.svg
outputs/demo_result.manifest.json
```

说明：

- `demo_result.svg` 是 mock 后端生成的占位示意图，不是真实照片。
- `demo_result.manifest.json` 会记录 prompt、参考图路径、语义解耦结果、控制器配置和输出路径。
- 示例路径即使没有真实图片，也可以跑通完整流程。

### 3. 使用配置文件生成

推荐使用 YAML 配置文件，便于阅读和修改：

```bash
uv run idpcg generate --config examples/generation_request.yaml
```

也可以直接通过命令行传参：

```bash
uv run idpcg generate \
  --fan-refs examples/assets/fan_01.jpg examples/assets/fan_02.jpg \
  --celebrity-refs examples/assets/star_01.jpg \
  --pose-image examples/assets/openpose_two_person.png \
  --prompt "a fan and a famous singer taking a friendly red-carpet photo" \
  --clothing-prompt "fan wearing a silver jacket, celebrity wearing a black stage suit" \
  --scene-prompt "cinematic red carpet, warm flash photography" \
  --use-style-lora \
  --output outputs/result.svg
```

## ComfyUI 部署

### 1. 启动 ComfyUI

如果 ComfyUI 安装在本仓库同级目录，也就是 `../ComfyUI`，可以直接使用脚本启动：

```powershell
.\scripts\start_comfyui.ps1
```

停止服务：

```powershell
.\scripts\stop_comfyui.ps1
```

浏览器访问：

```text
http://127.0.0.1:8188
```

检查 API 是否可用：

```bash
uv run idpcg comfyui-check --url http://127.0.0.1:8188
```

### 2. 生成 ComfyUI API Payload

默认配置只生成 payload，不提交任务：

```bash
uv run idpcg generate --config examples/comfyui_request.yaml
```

输出类似：

```text
outputs/comfyui_result.manifest.json
outputs/comfyui_result.comfyui_payload.json
```

确认 ComfyUI 已启动、checkpoint 文件名正确后，把配置里的 `submit_comfyui_job` 改为 `true`，即可提交真实任务。

### 3. 使用 LoRA + OpenPose 示例

```bash
uv run idpcg generate --config examples/comfyui_lora_openpose_request.yaml
```

这个配置用于验证现成模块组合链路：

- `v1-5-pruned-emaonly.safetensors`
- `lcm-lora-sdv1-5.safetensors`
- `control_v11p_sd15_openpose.safetensors`
- `workflows/comfyui_api_lora_openpose.json`

注意：这里的 LCM LoRA 是加速采样用的 LoRA，不是人物身份 LoRA。要做真正的身份保持，需要替换成自己训练的人物 LoRA。

### 4. 使用完整多控制器示例

```bash
uv run idpcg generate --config examples/comfyui_full_pipeline_request.yaml
```

这条链路会组合：

- LoRA：注入身份或采样风格。
- IP-Adapter：从参考图约束脸部结构。
- ControlNet：用 OpenPose 控制动作和站位。
- ComfyUI API workflow：`workflows/comfyui_api_full_pipeline.json`

首次运行建议先把分辨率设为 `512x512`、`batch_size` 设为 `1`，逐项确认模型能加载后再提高参数。

## 命令行说明

### 提取并解耦标签

```bash
uv run idpcg tag examples/assets/fan_01.jpg examples/assets/fan_02.jpg --role fan
```

输出包含：

- `raw`：原始视觉标签。
- `decoupled`：拆分后的身份、姿态、服装、背景标签。

### 准备 LoRA 训练清单

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

当前 `adapter_model.safetensors` 是占位文件。真实训练需要在 `src/id_preservation_cg/lora.py` 中实现 `LoraTrainer._run_real_training(...)`。

### 导出 ComfyUI 工作流模板

```bash
uv run idpcg workflow --output outputs/comfyui_workflow.json
```

导出可提交 `/prompt` 的基础 API workflow：

```bash
uv run idpcg workflow --kind api --output outputs/comfyui_api_txt2img.json
```

导出 LoRA + OpenPose ControlNet workflow：

```bash
uv run idpcg workflow --kind lora-openpose --output outputs/comfyui_api_lora_openpose.json
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

## 项目结构

```text
ID-Preservation-Controllable-Generation/
├── src/id_preservation_cg/    核心 Python 包
├── examples/                  示例配置、Demo 脚本和素材
├── workflows/                 ComfyUI 工作流模板
├── outputs/                   生成结果和运行记录
├── scripts/                   PowerShell 辅助脚本
├── tests/                     单元测试
├── docs/                      补充文档
├── pyproject.toml             项目元信息与依赖声明
└── README.md                  当前文档
```

核心模块：

| 文件 | 作用 |
| ---- | ---- |
| `tagging.py` | 模拟 WD14 标签提取，可替换为真实 tagger |
| `semantic.py` | 将标签拆分为身份、姿态、服装、背景 |
| `dataset.py` | 构建 LoRA caption 数据集，包含防过拟合策略 |
| `lora.py` | LoRA 训练门面和 manifest 生成 |
| `controllers.py` | 管理 LoRA、IP-Adapter、ControlNet、Style 控制器配置 |
| `pipeline.py` | 编排打标、解耦、控制器加载和后端生成 |
| `backends.py` | mock 后端、ComfyUI payload、任务提交和结果下载 |
| `cli.py` | `idpcg` 命令行入口 |
| `validation.py` | 请求参数校验 |

## 配置文件与工作流的区别

| 类型 | 位置 | 谁读取 | 用途 |
| ---- | ---- | ------ | ---- |
| 项目配置 | `examples/*.yaml` | `idpcg generate` | 描述参考图、prompt、控制器开关、输出路径和后端参数 |
| ComfyUI 工作流 | `workflows/*.json` | ComfyUI / ComfyUI API | 描述节点图、模型加载、采样器、ControlNet、IP-Adapter 等连接方式 |

一句话：配置文件告诉本项目“画什么”，工作流告诉 ComfyUI“怎么画”。

## 接入真实模型

推荐按下面顺序逐步替换，不要一开始就把所有模块同时接上：

1. 替换 `src/id_preservation_cg/tagging.py`，接入真实 WD14 或同类图像 tagger。
2. 替换 `src/id_preservation_cg/semantic.py`，接入 Qwen-VL、DeepSeek-VL 或其他 VLM，输出固定 schema。
3. 实现 `src/id_preservation_cg/lora.py` 中的真实 LoRA 训练逻辑。
4. 用 ComfyUI 导出自己的 API workflow，并在配置中设置 `model.comfyui_workflow`。
5. 如果不使用 ComfyUI，可以在 `src/id_preservation_cg/backends.py` 中新增 Diffusers 后端。

更多说明见：

```text
docs/REAL_BACKEND.md
docs/COMFYUI_BEGINNER_GUIDE.md
docs/SAFETY.md
```

## 测试

运行单元测试：

```bash
uv run python -m unittest discover -s tests
```

运行基础 smoke test：

```bash
uv run python examples/run_demo.py
uv run idpcg generate --config examples/generation_request.yaml
uv run idpcg generate --config examples/comfyui_request.yaml
```

## 常见问题

### 运行 demo 需要真实图片吗？

不需要。mock 模式允许示例路径不存在，适合先验证流程、配置结构和输出 manifest。

### 为什么生成的是 SVG，不是真照片？

因为默认后端是 `mock`。它用于离线验证工程链路，不执行真实扩散模型推理。要真出图，请把配置里的 `model.backend` 设为 `comfyui`，并确认 `submit_comfyui_job: true`。

### ComfyUI 提示找不到 checkpoint 怎么办？

确认模型文件已经放在 ComfyUI 的 `models/checkpoints/` 目录下，并且配置里的 `base_model` 和文件名完全一致，包括 `.safetensors` 后缀。

### 显存不够怎么办？

先使用 SD1.5、`512x512`、`batch_size: 1`，关闭不必要的控制器。等基础 workflow 稳定后，再逐步加入 LoRA、ControlNet 和 IP-Adapter。

### 这个项目已经能训练真实人物 LoRA 吗？

当前仓库提供训练清单、caption 构建和占位 adapter。真实训练需要接入 Diffusers、Accelerate 或你自己的训练脚本。

## 安全说明

真实人像生成属于敏感能力。正式使用前建议加入：

- 参考图授权和同意记录。
- 生成图水印或 AI 标识。
- prompt、seed、adapter、输出 hash 审计日志。
- 防冒充、防骚扰、防侵权、防虚假信息策略。
- 对真人、公众人物和未成年人内容的额外限制。

详见 [docs/SAFETY.md](docs/SAFETY.md)。

## 反馈建议

可以通过以下方式参与：

- 提交 [issue](https://github.com/Polaris-civil/ID-Preservation-Controllable-Generation/issues)。
- 提交 [pull request](https://github.com/Polaris-civil/ID-Preservation-Controllable-Generation/pulls)。
- 补充真实模型接入案例、ComfyUI workflow 或训练脚本。

## 许可证

Apache-2.0。详见 [LICENSE](LICENSE)。

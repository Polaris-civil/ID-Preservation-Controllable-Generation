# ComfyUI 与本项目新手操作指南

这份文档面向第一次使用 ComfyUI 的用户，目标是先跑通基础出图，再理解如何让本项目通过 API 调用 ComfyUI。

## 1. 环境准备

你需要在本机安装 ComfyUI。推荐放在本项目的同级目录（即 `../ComfyUI`），这样项目脚本可以自动定位。

ComfyUI 下载地址：<https://github.com/comfyanonymous/ComfyUI>

启动后浏览器访问：

```text
http://127.0.0.1:8188
```

下载至少一个 SD1.5 checkpoint（如 `v1-5-pruned-emaonly.safetensors`），放到 ComfyUI 的 `models/checkpoints/` 目录下。

## 2. 启动和停止 ComfyUI

启动：

```powershell
.\scripts\start_comfyui.ps1
```

停止：

```powershell
.\scripts\stop_comfyui.ps1
```

检查 API 是否就绪：

```powershell
uv run idpcg comfyui-check --url http://127.0.0.1:8188
```

如果返回 `"ok": true`，说明 ComfyUI API 可以被项目调用。

## 3. 在 ComfyUI 页面手动出第一张图

打开 `http://127.0.0.1:8188`，你会看到：

- 左侧：节点库、模型库、工作流模板。
- 中间：节点画布。
- 右侧：运行按钮、任务队列。

新手建议：

1. 点击左侧模板，选一个基础文生图模板。
2. 确认 Checkpoint 节点选择了正确的模型（如 `v1-5-pruned-emaonly.safetensors`）。
3. 在正向 prompt 文本框填：
   ```
   two people smiling backstage, realistic portrait, soft light, high quality
   ```
4. 在反向 prompt 文本框填：
   ```
   low quality, blurry, distorted face, bad anatomy
   ```
5. 参数建议：
   ```
   width: 512
   height: 512
   steps: 20-25
   cfg: 7
   batch size: 1
   sampler: dpmpp_2m
   scheduler: karras
   ```
6. 点击运行，等待任务完成。

## 4. 用本项目调用 ComfyUI 出图

配置文件：

```text
examples/comfyui_request.yaml
```

确认关键字段：

```yaml
model:
  backend: comfyui
  base_model: "v1-5-pruned-emaonly.safetensors"  # 与 ComfyUI 中显示的文件名一致
  comfyui_url: "http://127.0.0.1:8188"
  submit_comfyui_job: true    # 改为 true 才会真正提交任务
  width: 512
  height: 512
  steps: 25
```

运行：

```bash
uv run idpcg generate --config examples/comfyui_request.yaml
```

输出文件：

```text
outputs/comfyui_result.png               ← 生成图
outputs/comfyui_result.manifest.json     ← 本项目记录的完整生成信息
outputs/comfyui_result.comfyui_payload.json   ← 提交给 ComfyUI 的 API workflow
outputs/comfyui_result.comfyui_history.json   ← ComfyUI 返回的任务历史
```

## 5. ComfyUI 和本项目分别负责什么

**ComfyUI 负责：**

- 加载 checkpoint。
- 执行采样。
- 管理节点工作流。
- 生成图片。

**本项目负责：**

- 从参考图生成标签。
- 将标签拆成 ID、姿态、服装、背景。
- 组织 prompt。
- 准备 LoRA 训练清单。
- 通过 API 把任务提交给 ComfyUI。
- 保存 manifest，方便复现实验。

## 6. 下一步：ID 保持与可控生成

当前跑通的是基础文生图。如果暂时不训练自己的 LoRA，可以先跑现成模块组合：

```bash
uv run idpcg generate --config examples/comfyui_lora_openpose_request.yaml
```

这个配置会用到：

- LCM LoRA（加速采样）
- OpenPose ControlNet（控制姿态）
- SD1.5 checkpoint
- 双人 OpenPose 姿态图

输出：`outputs/comfyui_lora_openpose.png`

这一步用于验证模块组合链路，不代表已经具备"指定真人 ID 保持"能力。

要做真正的 ID 保持和动作控制，还需要逐步加：

1. **LoRA**：把少量粉丝参考图训练成身份 adapter。
2. **IP-Adapter**：用参考图约束人脸结构。
3. **ControlNet OpenPose**：用姿态图控制合照动作。
4. **自定义 ComfyUI API workflow**：把 LoRA、IP-Adapter、ControlNet 节点接进工作流。

建议顺序：

```text
基础 txt2img 出图
  → 加 LoRA
  → 加 OpenPose ControlNet
  → 加 IP-Adapter
  → 接入本项目自动生成 prompt 与 API 调用
```

不要一开始就同时上所有模块。先保证每一步单独能出图，再组合。

## 7. 显卡与参数建议

**入门（SD1.5）：**

```text
512x512
batch size 1
steps 20-30
```

**进阶（SDXL）：**

```text
1024x1024 可尝试
batch size 1
必要时降到 768x768 或开启低显存策略
```

**多控制器组合：**

```text
SD1.5 + LoRA + ControlNet + IP-Adapter 更稳
SDXL + 多控制器显存压力较大，需逐项测试
```

## 8. 常见问题

### ComfyUI 页面打不开

先检查服务：

```powershell
uv run idpcg comfyui-check --url http://127.0.0.1:8188
```

如果失败，重新启动：

```powershell
.\scripts\start_comfyui.ps1
```

### 提示找不到 checkpoint

确认模型文件在 ComfyUI 的 `models/checkpoints/` 目录下，并且配置里的 `base_model` 与文件名完全一致（包括 `.safetensors` 后缀）。

### 显存不够

先降低参数：

```text
width: 512
height: 512
batch_size: 1
steps: 20
```

并关闭浏览器、聊天软件等占显存程序。

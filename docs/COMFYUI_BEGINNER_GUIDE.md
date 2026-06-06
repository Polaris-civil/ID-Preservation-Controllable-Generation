# ComfyUI 与本项目新手操作指南

这份文档面向第一次使用 ComfyUI 的用户，目标是先跑通基础出图，再理解如何让本项目通过 API 调用 ComfyUI。

## 1. 你当前已经具备的环境

ComfyUI 安装位置：

```text
E:\trae\AIGC_github\ComfyUI
```

本项目位置：

```text
E:\trae\AIGC_github\ID-Preservation-Controllable-Generation
```

ComfyUI 地址：

```text
http://127.0.0.1:8188
```

已下载模型：

```text
E:\trae\AIGC_github\ComfyUI\models\checkpoints\v1-5-pruned-emaonly.safetensors
```

这个模型是 SD1.5，适合 RTX 4060 8GB 先练手。

## 2. 启动和停止 ComfyUI

在 PowerShell 中进入项目目录：

```powershell
cd E:\trae\AIGC_github\ID-Preservation-Controllable-Generation
```

启动：

```powershell
.\scripts\start_comfyui.ps1
```

停止：

```powershell
.\scripts\stop_comfyui.ps1
```

检查 API：

```powershell
idpcg comfyui-check --url http://127.0.0.1:8188
```

如果返回 `"ok": true`，说明 ComfyUI API 可以被项目调用。

## 3. 在 ComfyUI 页面手动出第一张图

打开：

```text
http://127.0.0.1:8188
```

页面上你会看到：

- 左侧：资产、节点库、模型库、工作流、模板。
- 中间：节点画布。
- 右侧或浮动区域：运行按钮、任务队列。

新手建议使用模板：

1. 点击左侧 `模板`。
2. 找一个基础文生图或 SD1.5 文生图模板。
3. 加载模板后，确认 Checkpoint 节点选择：

```text
v1-5-pruned-emaonly.safetensors
```

4. 找到正向 prompt 文本框，填：

```text
two people smiling backstage, realistic portrait, soft light, high quality
```

5. 找到反向 prompt 文本框，填：

```text
low quality, blurry, distorted face, bad anatomy
```

6. 参数建议：

```text
width: 512
height: 512
steps: 20-25
cfg: 7
batch size: 1
sampler: dpmpp_2m
scheduler: karras
```

7. 点击 `运行`。
8. 等待右侧任务完成，输出图会显示在 SaveImage 或预览节点里。

## 4. 用本项目调用 ComfyUI 出图

项目里已经有配置文件：

```text
examples/comfyui_request.json
```

先确认里面这些字段：

```json
{
  "model": {
    "backend": "comfyui",
    "base_model": "v1-5-pruned-emaonly.safetensors",
    "comfyui_url": "http://127.0.0.1:8188",
    "submit_comfyui_job": true,
    "width": 512,
    "height": 512,
    "steps": 25
  }
}
```

运行：

```powershell
cd E:\trae\AIGC_github\ID-Preservation-Controllable-Generation
idpcg generate --config examples\comfyui_request.json
```

输出会在：

```text
outputs\comfyui_result.png
outputs\comfyui_result.manifest.json
outputs\comfyui_result.comfyui_payload.json
outputs\comfyui_result.comfyui_history.json
```

其中：

- `.png` 是生成图。
- `.manifest.json` 是本项目记录的完整生成信息。
- `.comfyui_payload.json` 是提交给 ComfyUI 的 API workflow。
- `.comfyui_history.json` 是 ComfyUI 返回的任务历史。

## 5. ComfyUI 和本项目分别负责什么

ComfyUI 负责：

- 加载 checkpoint。
- 执行采样。
- 管理节点工作流。
- 生成图片。

本项目负责：

- 从参考图生成标签。
- 将标签拆成 ID、姿态、服装、背景。
- 组织 prompt。
- 准备 LoRA 训练清单。
- 通过 API 把任务提交给 ComfyUI。
- 保存 manifest，方便复现实验。

## 6. 下一步：ID 保持与可控生成

当前已经跑通的是基础文生图。

要做真正的 ID 保持和动作控制，还需要逐步加：

1. LoRA：把少量粉丝参考图训练成身份 adapter。
2. IP-Adapter：用参考图约束人脸结构。
3. ControlNet OpenPose：用姿态图控制合照动作。
4. 自定义 ComfyUI API workflow：把 LoRA、IP-Adapter、ControlNet 节点接进工作流。

建议顺序：

```text
基础 txt2img 出图
  -> 加 LoRA
  -> 加 OpenPose ControlNet
  -> 加 IP-Adapter
  -> 接入本项目自动生成 prompt 与 API 调用
```

不要一开始就同时上 LoRA、IP-Adapter、ControlNet。先保证每一步单独能出图，再组合。

## 7. RTX 4060 8GB 推荐参数

SD1.5：

```text
512x512
batch size 1
steps 20-30
```

SDXL：

```text
1024x1024 可以尝试
batch size 1
必要时降低到 768x768 或开启低显存策略
```

多控制器组合：

```text
SD1.5 + LoRA + ControlNet + IP-Adapter 更稳
SDXL + 多控制器可能显存紧张
```

## 8. 常见问题

### ComfyUI 页面打不开

先检查服务：

```powershell
idpcg comfyui-check --url http://127.0.0.1:8188
```

如果失败，重新启动：

```powershell
.\scripts\start_comfyui.ps1
```

### 提示找不到 checkpoint

确认模型文件在：

```text
E:\trae\AIGC_github\ComfyUI\models\checkpoints
```

并且配置里的 `base_model` 与文件名完全一致。

### 显存不够

先改小：

```text
width: 512
height: 512
batch_size: 1
steps: 20
```

并关闭浏览器、PPT、Word、聊天软件等占显存程序。

# Changelog

所有重要变更记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [0.1.0] — Unreleased

### Added

- WD14-like 离线图像打标器，支持批量提取标签
- 多模态语义重构器，将标签解耦为 ID / 姿态 / 服装 / 背景四类
- 少样本 LoRA 训练门面，内置 Prompt Dropout 和标签扰动防过拟合
- IP-Adapter 控制器，约束人脸结构与身份一致性
- ControlNet OpenPose 控制器，支持骨骼图控制人物姿态
- Style 控制器，控制服装和场景风格
- Mock SVG 后端，无需大模型即可跑通完整流程
- ComfyUI API 后端，支持真实出图、上传参考图、轮询结果、下载输出
- `idpcg` CLI：`tag`、`generate`、`train-lora`、`workflow`、`comfyui-check` 命令
- YAML 格式配置文件，支持注释，与 JSON 格式并存
- ComfyUI 工作流模板：txt2img、LoRA+OpenPose、LoRA+IP-Adapter+ControlNet 全管线
- 自动启动/停止 ComfyUI 的 PowerShell 脚本（`scripts/`）
- GitHub Actions CI，使用 uv 构建，覆盖 Python 3.9 / 3.10 / 3.12

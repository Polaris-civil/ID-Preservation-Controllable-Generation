# Contributing

欢迎贡献！本文档帮你快速上手。

## 环境搭建

```bash
# 安装开发依赖
uv sync --extra dev
```

## 项目架构

```
src/id_preservation_cg/
├── cli.py           ← 命令行入口（tag / generate / train-lora / workflow）
├── config.py        ← 所有数据结构定义（GenerationRequest, ModelConfig, ControlConfig）
├── pipeline.py      ← 端到端生成编排（打标 → 解耦 → 控制器 → 后端）
├── tagging.py       ← 图像打标器接口（当前为模拟版）
├── semantic.py      ← 多模态语义解耦（ID / 姿态 / 服装 / 背景）
├── controllers.py   ← 控制器抽象（IPAdapter / ControlNet / Style）
├── lora.py          ← LoRA 训练门面
├── dataset.py       ← 训练数据集构建（caption 生成、防过拟合）
├── backends.py      ← 生成后端（Mock SVG / ComfyUI API）
└── validation.py    ← 输入校验
```

## 检查清单

```bash
# Smoke test（离线全流程）
uv run python examples/run_demo.py

# 用 YAML 配置生成（需本地 ComfyUI 运行）
uv run idpcg generate --config examples/comfyui_request.yaml

# 单元测试
uv run python -m unittest discover -s tests
```

## 如何添加新功能

### 添加新控制器

1. 在 `controllers.py` 中继承 `BaseController`，实现 `apply()` 方法
2. 在 `pipeline.py` 的 `_build_controllers()` 中注册
3. 在 `ControlConfig` 中添加对应的 `use_xxx` 开关
4. 在 `ModelConfig` 中添加对应的模型文件名字段

### 添加新后端

1. 在 `backends.py` 中创建新类，实现 `render()` 方法
2. 在 `backend_for_request()` 中注册新后端的名称映射
3. 确保新后端也输出 manifest JSON

### 接入真实模型

- 真实 WD14 Tagger → 替换 `tagging.py`，保持返回值不变
- 真实 VLM 语义重构 → 替换 `semantic.py`，保持输出 schema 不变
- 真实 LoRA 训练 → 在 `lora.py` 的 `_run_real_training()` 中接入 Diffusers/Accelerate

## 设计原则

- **离线 Mock 优先**：不下载大模型也能跑通全流程
- **Schema 稳定**：修改 `GenerationRequest` 和 manifest 结构时保持向后兼容
- **真实模型放 optional extras**：训练和推理依赖放在 `full` extras 里
- **测试覆盖关键路径**：CLI 契约、配置解析、pipeline 输出格式

## Pull Request 规范

- 新功能请附带测试
- 修改 CLI 接口请同步更新 README 示例
- 提交信息使用英文，格式：`<动词> <简短描述>`，如 `Add ControlNet depth controller`
- 先在本地跑通 `uv run python -m unittest discover -s tests` 再提交

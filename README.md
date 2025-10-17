# Pivot

Pivot 是一个面向 GitHub 技术文档的持续本地化工具，旨在以 CI/CD 的方式同步英文文档到中文译文。项目会监控指定仓库中的 Markdown 与 YAML 文件，侦测新增或修改的内容，将其中的自然语言片段翻译成中文，并输出到镜像目录结构中，同时保留代码块与格式。

> 当前仓库处于早期开发阶段，已完成项目骨架、配置系统、仓库同步与变更检测模块。

## 功能概览

- 🧩 **模块化架构**：CLI 调度、配置、仓库管理、变更检测等模块相互解耦，便于后续扩展翻译、输出等能力。
- ⚙️ **可配置化**：通过 YAML 配置文件或环境变量指定工作目录、输出路径、目标仓库以及翻译提供方参数。
- 🔄 **仓库同步**：使用 GitPython 克隆或拉取目标仓库，保持本地缓存与远端分支一致。
- 🧭 **文档差异检测**：基于上次同步的提交指针，智能筛选 Markdown / YAML 变更，过滤非文档路径。
- ✅ **质量基线**：集成 `ruff`、`mypy`、`pytest` 作为开发期质量保障。

## 快速上手

### 先决条件

- Python 3.11+
- Git 2.30+

### 安装依赖

```bash
make install
```

该命令会升级 `pip` 并安装项目及开发依赖（`ruff`、`mypy`、`pytest` 等）。

### 编写配置文件

在项目根目录创建 `pivot.yaml`（或通过 `PIVOT_CONFIG` 环境变量指向任意路径）：

```yaml
work_dir: ./var/cache
output_dir: ./var/output
repositories:
  - name: docs
    url: https://github.com/example/docs-repo
    branch: main
    docs_path: docs
translation:
  provider: openai
  model: gpt-4o
  base_url: https://api.openai.com/v1
  api_key_env: OPENAI_API_KEY
```

> `translation.api_key` 可以直接写在配置中，也可以通过 `translation.api_key_env` 指定环境变量。两者至少需要一个。

### 验证配置

```bash
pivot validate-config --config pivot.yaml
```

命令会解析配置、创建工作目录，并打印已登记的仓库信息。

### 运行（占位版）

```bash
pivot run --config pivot.yaml
```

当前 `run` 命令处于 dry-run 模式，会同步仓库并列出检测到的文档变更；后续迭代将补全实际翻译与输出流水线。

## 开发指南

执行常用开发任务：

```bash
make format    # 使用 ruff format
make lint      # 使用 ruff check
make typecheck # 使用 mypy
make test      # 运行 pytest
make check     # 依次执行 format+lint+typecheck+test
```

建议在提交 PR 前运行 `make check`，并确保测试全部通过。

## 当前路线图

1. 集成翻译 Provider（OpenAI 兼容接口）与内容分块策略。
2. 构建 Markdown / YAML 精细解析与重组模块，保留代码块及格式。
3. 实现译文输出目录镜像与命名规范（`{原始文件名}-{中文翻译}.{扩展名}`）。
4. 引入流水线状态持久化与增量处理回放能力。
5. 打通 CLI 全流程并加入定时任务/守护进程支持。

欢迎通过 Issue / PR 提出建议或参与贡献。

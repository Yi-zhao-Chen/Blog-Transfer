# al-folio模板博客转化器

> **注意**：
>
> - 因为作者偷懒，这个仓库几乎全部靠vibe coding得到，且没有经过完全的人工审核，所以可能会有没被捕捉的错误。
> - 代码中可能的问题和修改方向由大语言模型生成，可以参考文档[Modifications.md](Modifications.md).
> - 暂定的升级方向：
>
> 1. 处理完全使用LaTeX编码的文件
> 2. 处理文件重复的情形
> 3. 检查引用和多重引用时是否留有空行（目前的代码仅在保留空行时正常运行）
> 4. 一次性处理多个文件。
> 5. 图形界面(GUI)的美化。
>
> 同样因为作者懒，所以下面的说明文本在大语言模型生成的基础上略作修改得到。

这是一个基于 PyQt5 的桌面应用程序，用于将 Markdown 或 PDF 文件转换为带有 YAML front matter 的标准化 Markdown 文档，适用于 Jekyll、Hugo 等静态网站生成器。具体而言，是用于生成网页模板[al-folio](https://github.com/alshedivat/al-folio)中博客使用的 Markdown 文档。生成方式分为两种：

- 将 Markdown 文件直接变为博客需要的 Markdown 文件。
- 将 pdf 文件变为重定向的 Markdown 文件。

**目录**

[主要功能](##主要功能)

[安装与运行](##安装与运行)

[项目结构](##项目结构)

[使用流程](##使用流程)

[输出文件格式](##输出文件格式)

[技术细节](##技术细节)

[测试](##测试)

[注意事项](##注意事项)

## 主要功能

- **Markdown 文件处理**：
  - 自动提取一级标题作为默认标题
  - 转换数学公式为 MathJax 兼容格式
  - 生成包含布局（默认为`post`）、标题、日期（基于原始文件的最后编辑时间）等元数据的 YAML front matter
  - 添加自动目录功能
  - 图片自动处理：识别本地图片并复制到 `assets/img/posts/{文章文件名}/` 目录，将原始 `![alt](path)` 语法自动转换为 al-folio 兼容的 Liquid 标签（`{% include figure.liquid %}`），支持网络图片直接引用。

- **PDF 文件处理**：
  - 复制 PDF 文件到资源目录
  - 生成重定向 front matter 指向 PDF 文件
  - 自动处理文件名冲突

- **图形用户界面**：
  - 文件选择和目录浏览
  - 元数据编辑（标题、描述、标签）
  - 记住上次操作路径
  - 成功/错误提示

## 安装与运行

### 依赖安装

程序使用的语言为Python，可以在几乎不额外安装其他库的情况下运行。唯一需要额外安装的库是PyQt5：

```bash
pip install PyQt5
```

### 运行应用程序

```bash
python main.pyw
```

（双击main.pyw也行）

## 项目结构

```text
├── config.py                # 配置文件（PDF存储路径、公式格式）
├── converter.py             # LaTeX公式转换器（MathJax兼容）
├── file_processor.py        # 核心文件处理逻辑
├── gui.py                   # PyQt5图形用户界面
├── main.pyw                 # 应用程序入口
├── test_manual.py           # 手动测试脚本
└── tools/
    └── MyYaml.py            # 自定义YAML导出工具
```

## 使用流程

1. **选择输入文件**：
   - 支持 Markdown (.md) 或 PDF (.pdf) 文件
   - Markdown 文件自动提取一级标题

2. **编辑元数据**：
   - 标题（必填）
   - 描述（必填）
   - 标签（逗号或空格分隔，可选）
   - 选择输出目录

3. **生成文件**：
   - Markdown 文件：生成带 front matter 的标准文档
   - PDF 文件：生成重定向文档并复制 PDF 到资源目录

## 输出文件格式

### Markdown 处理结果

```yaml
---
layout: post
title: "文章标题"
date: 2025-07-18 12:00:00
description: "文章描述"
tags: [标签1, 标签2]
categories: Notes
toc:
  beginning: true
---

<!-- 转换后的Markdown内容 -->
```

### PDF 处理结果

```yaml
---
layout: post
title: "PDF文档标题"
date: 2025-07-18 12:00:00
redirect: "../assets/pdf/posts/filename.pdf"
categories: Notes
---
```

## 技术细节

- **数学公式处理**：
  - 支持行内公式 (`$...$`) 和块级公式 (`$$...$$`)
  - 自动转义特殊字符（`|` → `\vert`）
  - 自动处理上下标格式（`x^2` → `x^{2}`）

- **图片处理**：
  - 自动识别 Markdown 中的图片引用语法 `![alt](path)`
  - 本地图片（相对/绝对路径）会被复制到 `assets/img/posts/{输出文件名（去扩展名）}/` 目录
  - 重复引用同一张图片只复制一次，避免冗余
  - 网络图片（http/https）保持原 URL 不变，仅替换为 Liquid 模板
  - 图片渲染模板可在 `config.py` 中的 `image_render_template` 变量统一配置
  - 仅当存在本地图片时才会创建目标子目录，避免生成空文件夹

- **文件命名规范**：
  - `年-月-日-标题-slug.md`
  - 标题中的空格替换为连字符
  - 移除特殊字符

- **智能空行处理**：
  - 保留引用层级（`>` 符号）
  - 合并连续空行

## 测试

运行手动测试脚本：

```bash
python test_manual.py
```

测试内容包括：

- Markdown 文件处理流程
- PDF 文件处理流程
- 公式转换功能
- 文件名生成规则

## 注意事项

1. 数学公式中的 `$` 和 `\` 符号需要正确转义
2. PDF 文件会复制到 `../assets/pdf/posts/` 目录
3. 输出文件名中的特殊字符会被自动过滤
4. 应用会记住上次使用的目录路径
5. 关于图片处理：
   - 确保本地图片路径正确（支持相对于 `.md` 文件的路径或绝对路径），否则图片会被保留原语法并输出警告
   - 图片文件名冲突时会自动添加数字后缀（如 `image_1.png`）
   - 输出目录下的图片相对路径会自动计算并写入模板中
   - 若不需要图片子目录结构，可修改 `_process_images` 中的 `dest_root` 定义

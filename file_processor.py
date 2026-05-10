# file_processor.py
import re,os.path,os,shutil
from datetime import datetime
from pathlib import Path

import converter
from tools.MyYaml import dump as yaml_dump
from config import pdf_storage_dir,table_of_content_info,posts_img_storage_dir, image_render_template


class FileProcessor:
    """核心文件处理逻辑（无 GUI 依赖）
    
    提供静态方法处理不同类型的输入文件（目前支持 .md 和 .pdf），
    将其转换为符合规范的 Markdown 文件，并添加元数据（front matter）。
    
    主要功能：
      1. 处理 Markdown 文件：
          - 提取原始标题并移除标题行
          - 转换数学公式（MathJax 格式）
          - 生成包含布局/标题/日期等元数据的 YAML front matter
      2. 处理 PDF 文件：
          - 将 PDF 复制到指定资源目录
          - 生成重定向 front matter（指向 PDF 文件）
      3. 自动生成规范化文件名：`年-月-日-标题-slug.md`
      4. 提供从 Markdown 文件快速提取标题的辅助方法
    
    使用示例：
      >>> output_path = FileProcessor.process_file(
            input_path="/path/to/input.md",
            output_dir="/path/to/output",
            metadata={
                "title": "新标题",
                "description": "文件描述",
                "tags": ["标签1", "标签2"]
            }
        )
    """

    @staticmethod
    def process_file(input_path: str, output_dir: str, metadata: dict) -> str:
        """
        处理输入文件并生成标准化的Markdown输出
        
        根据文件类型调用不同的处理方法，生成包含YAML front matter的Markdown文件。
        自动处理文件名生成和输出目录创建。
        
        :param input_path: 输入文件路径（支持.md和.pdf）
        :param output_dir: 输出目录路径
        :param metadata: 元数据字典，包含以下键：
            - title: 文章标题
            - description: 文章描述
            - tags: 标签列表（可选）
            - layout: 布局类型（可选，默认'post'）
            - categories: 分类（可选，默认'Notes'）
        :return: 生成的Markdown文件完整路径
        :raises ValueError: 当遇到不支持的文件类型时
        :raises 其他异常: 文件操作或处理过程中可能出现的异常
        """
        # 将metadata['title']中的冒号替换为'-'
        metadata['title'] = re.sub(r':+', '-', metadata['title']).strip()

        metadata['time'] = datetime.fromtimestamp(
            os.path.getmtime(input_path)).strftime("%Y-%m-%d %H:%M:%S")

        _, ext = os.path.splitext(input_path.lower())
        filename = FileProcessor._generate_filename(metadata)
        if ext == '.md':
            # 先产生文件名和 stem
            output_stem = Path(filename).stem
            front_matter, body = FileProcessor._handle_markdown(
                input_path, output_dir, output_stem, metadata
            )
        elif ext == '.pdf':
            front_matter, body = FileProcessor._handle_pdf(input_path, output_dir, metadata)
        else:
            raise ValueError(f"不支持的文件类型：{ext}")

        os.makedirs(output_dir, exist_ok=True)
        dest = Path(output_dir) / filename
        with open(dest, 'w', encoding='utf-8') as f:
            f.write('---\n')
            f.write(front_matter)
            f.write('---\n')
            if body:
                f.write(body)
        return str(dest)

    # 供 GUI 快速提取标题
    @staticmethod
    def extract_title_from_md(path: str) -> str | None:
        """
        从Markdown文件中快速提取一级标题
        
        用于GUI预填充标题字段，不处理文件内容
        
        :param path: Markdown文件路径
        :return: 提取的标题（找到一级标题时）或None（未找到时）
        """
        with open(path, encoding='utf-8') as f:
            m = re.search(r'^#\s+(.+)$', f.read(), re.MULTILINE)
        return m.group(1).strip() if m else None

    # ---------- 私有工具 ----------
    @staticmethod
    def _process_images(content: str, input_md_dir: str, output_dir: str, output_stem: str) -> str:
        """
        处理 Markdown 中的图片引用：
        - 复制本地图片到 assets/img/posts/{output_stem}/ 目录
        - 将原始图片语法替换为 al-folio 的 figure.liquid 模板
        - 保留网络图片引用（不复制，只替换模板）
        - 重复引用的同一张图片只复制一次
        - 仅当存在需要复制的本地图片时才创建目标目录
        """

        # 目标根目录：网站根目录/assets/img/posts/{output_stem}/
        website_root = Path(output_dir).parent
        dest_root = website_root / posts_img_storage_dir / output_stem

        # 缓存：源文件绝对路径 -> 相对路径（从 output_dir 到目标图片）
        image_cache = {}
        # 标记是否已经创建目录
        dir_created = False

        def ensure_dir():
            """确保图片目标目录存在"""
            nonlocal dir_created
            if not dir_created:
                dest_root.mkdir(parents=True, exist_ok=True)
                dir_created = True

        def replace_image(match):
            nonlocal dir_created
            alt = match.group(1) # alt是md代码中对图片的描述
            raw_path = match.group(2).strip()

            # 网络图片：不复制，直接使用原始路径
            if raw_path.startswith(('http://', 'https://')):
                return image_render_template.format(raw_path)

            # 本地图片：解析绝对路径
            if os.path.isabs(raw_path):
                src = raw_path
            else:
                src = os.path.join(input_md_dir, raw_path)

            if not os.path.exists(src):
                print(f"警告：图片不存在 - {src}，将保留原始语法")
                return match.group(0)  # 保留原样

            # 检查是否已处理过该图片
            if src in image_cache:
                rel_path = image_cache[src]
                return image_render_template.format(rel_path)

            # 首次复制本地图片时创建目录
            ensure_dir()

            # 复制图片到目标文件夹，处理重名
            base_name = os.path.basename(src)
            dest_path = dest_root / base_name
            counter = 1
            while dest_path.exists():
                stem, ext = os.path.splitext(base_name)
                new_name = f"{stem}_{counter}{ext}"
                dest_path = dest_root / new_name
                counter += 1
            shutil.copy2(src, dest_path)

            # 计算从输出 .md 文件到图片的相对路径
            rel_path = os.path.relpath(dest_path, start=output_dir).replace(os.sep, '/')
            # 存入缓存
            image_cache[src] = rel_path
            return image_render_template.format(rel_path)

        # 匹配所有图片语法 ![alt](path)
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        return re.sub(pattern, replace_image, content)

    @staticmethod
    def _handle_markdown(input_path: str, output_dir: str, output_stem: str, metadata: dict):
        """
        处理Markdown文件的内部方法
        
        执行以下操作：
        1. 提取并移除原始文件的一级标题
        2. 处理markdown中的图片引用
        3. 转换数学公式（MathJax格式）
        4. 构建YAML front matter
        
        :param input_path: Markdown文件路径
        :param output_dir: 生成的Markdown文件路径(用于复制图片)
        :param output_stem: 生成Markdown文件名(用于复制图片)
        :param metadata: 元数据字典（将被增强）
        :return: (front_matter, body)元组
            - front_matter: 生成的YAML格式字符串
            - body: 处理后的Markdown内容
        :raises ValueError: 当找不到一级标题时
        """
        with open(input_path, encoding='utf-8') as f:
            content = f.read()

        # 提取标题
        m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if not m:
            raise ValueError("未找到一级标题（# Title）")
        title = m.group(1).strip()
        # 上一行代码不知道有什么用

        # 移除原文标题行
        content = re.sub(r'^#\s+.+$', '', content, count=1, flags=re.MULTILINE)

        # 移除原文目录
        content = re.sub(
            r'(?si)(?:\n*\[TOC\]\n*|\n*\[\[TOC\]\]\n*|\n*\{:\s*toc\s*\}\n*|'
            r'\n*\[toc\]\n*|\n*\[ToC\]\n*|\n*\[to[cC]\]\n*|'
            r'(?:(?:^|\n)(?: {0,3}-| {0,3}\d+\.) .*\n)+(?=\n*#))',
            '\n',
            content
        )

        # 处理图片
        content = FileProcessor._process_images(
            content,
            os.path.dirname(input_path),
            output_dir,
            output_stem
        )

        # 公式转换
        body = converter.MathJax_Converter().convert(content)

        front_matter = {
            'layout': metadata.get('layout', 'post'),
            'title': metadata['title'],
            'date': metadata['time'],
            'description': metadata['description'],
            'tags': metadata.get('tags', []),
            'categories': metadata.get('categories', 'Notes'),
            'toc': table_of_content_info
        }
        return yaml_dump(front_matter), body

    @staticmethod
    def _handle_pdf(input_path: str, output_dir: str, metadata: dict):
        """
        处理PDF文件的内部方法
        
        执行以下操作：
        1. 复制PDF文件到output_dir父级目录的assets/pdf/posts目录（自动解决重名冲突）
        2. 构建重定向用的YAML front matter
        
        :param input_path: PDF文件路径
        :param output_dir: 输出目录
        :param metadata: 元数据字典
        :return: (front_matter, body)元组
            - front_matter: 生成的YAML格式字符串
            - body: 空字符串（PDF处理不生成正文内容）
        """
        base_dir = Path(output_dir).parent
        dest_dir = base_dir / pdf_storage_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        pdf_name = Path(input_path).name
        dest_path = dest_dir / pdf_name

        # 解决重名
        counter = 1
        while dest_path.exists():
            stem, suffix = Path(pdf_name).stem, Path(pdf_name).suffix
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.copy2(input_path, dest_path)

        # 计算相对路径（pdf存储位置相对于output_dir）
        rel_path = os.path.relpath(dest_path, start=output_dir)
        rel_path = rel_path.replace(os.sep, '/')

        front_matter = {
            'layout': 'post',
            'title': metadata['title'],
            'date': metadata['time'],
            'description': metadata['description'],
            'tags': metadata.get('tags', []),
            'categories': metadata.get('categories', 'Notes'),
            'redirect': rel_path
        }
        return yaml_dump(front_matter), ""

    @staticmethod
    def _generate_filename(metadata):
        """
        生成标准化文件名
        
        文件名格式：YYYY-MM-DD-标题-slug.md
        标题处理规则：
          1. 日期部分取自元数据的'time'字段
          2. 标题中的空格替换为连字符(-)
          3. 移除特殊字符
        
        :param metadata: 元数据字典（需包含'title'和'time'）
        :return: 生成的标准化文件名
        """
        date_str = datetime.strptime(metadata['time'],"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        title_slug = re.sub(r'[\\/:\*\?"<>\|\s]+', '-', metadata['title']).strip().strip('-')
        return f"{date_str}-{title_slug}.md"
    
if __name__ == '__main__':
    d = {'time':'2012-03-12 12:22:12','title':'12啊12 12.12'}
    print(FileProcessor._generate_filename(d))
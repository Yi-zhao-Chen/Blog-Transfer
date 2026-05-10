# pdf的默认存储目录
pdf_storage_dir = r'assets/pdf/posts'

# 以下参数设置输入公式的格式（与MathJax 3相容），分行内公式(inline)和行间公式(block)，行间公式分标号和不标号两种
standard_output_style = {
    'math_inline_surrounding':'$$',
    'math_block_begin':"$$",
    'math_block_end':"$$\n"
    }

# 储存Blog图片的位置
posts_img_storage_dir = r'assets/img/posts'
# 图片渲染样式
image_render_template = '''
<div>
    {{% include figure.liquid loading="eager" path="{}" class="img-fluid rounded z-depth-1" zoomable=true %}}
</div>
'''

# 控制目录样式（`{'beginning': True}`对应从头开始的目录，`{'sidebar':'left',}`对应位于左侧单独成栏的目录）
table_of_content_info = {'sidebar':'left',}
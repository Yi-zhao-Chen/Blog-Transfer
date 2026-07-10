# gui.py  (PyQt5)
"""
? PyQt5 GUI 组件说明

本文件使用 PyQt5 框架构建图形用户界面，主要包含以下组件：

1. 核心类:
   - QMainWindow: 主窗口基类，提供菜单栏/状态栏/中央部件等标准结构
   - QWidget: 通用窗口部件基类
   - QLabel: 文本标签显示
   - QPushButton: 可点击按钮
   - QLineEdit: 单行文本输入框
   - QTextEdit: 多行文本编辑区
   - QMessageBox: 信息提示对话框（错误/成功提示）

2. 布局管理器:
   - QVBoxLayout: 垂直布局（控件从上到下排列）
   - QHBoxLayout: 水平布局（控件从左到右排列）

3. 对话框组件:
   - QFileDialog: 文件选择对话框
     * getOpenFileName(): 打开单个文件
     * getExistingDirectory(): 选择目录

4. 配置管理:
   - QSettings: 应用程序设置持久化
     * value(): 读取设置值
     * setValue(): 保存设置值

5. 信号与槽机制:
   - clicked 信号: 按钮点击事件处理
   - 自定义槽函数: 以 _ 开头的内部处理方法

界面结构:
  主窗口包含以下功能区:
  1. 文件选择区
  2. 标题/描述/标签输入区
  3. 输出目录选择区
  4. 生成文章提交区

用户交互流程:
  选择文件 → 填充标题 → 填写元数据 → 选择输出目录 → 提交生成
"""

import os,re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSettings  # 用于记住上次路径


class MainWindow(QMainWindow):
    # 改为 QMainWindow 便于扩展
    def __init__(self, on_file_select, on_submit):
        """
        初始化主窗口
        
        创建GUI界面并设置相关功能：
        1. 保存回调函数：on_file_select（文件选择回调）和 on_submit（提交回调）
        2. 初始化设置（QSettings），用于记住用户上次选择的目录
        3. 调用 _init_ui 方法创建界面元素
        
        :param on_file_select: 文件选择时触发的回调函数
        :param on_submit: 表单提交时触发的回调函数
        """
        super().__init__()
        self.on_file_select = on_file_select
        self.on_submit = on_submit
        self.settings = QSettings("my_org", "md_pdf_poster")
        # 分别读取文件选择目录和输出目录
        self._last_file_dir = self.settings.value("last_file_dir", os.getcwd())
        self._last_out_dir = self.settings.value("last_out_dir", os.getcwd())
        self._init_ui()

    # ---------- 界面初始化 ----------
    def _init_ui(self):
        """
        初始化用户界面
        
        创建并布局所有UI组件：
        1. 文件选择区域（按钮+标签）
        2. 标题输入框
        3. 描述文本区域
        4. 标签输入框（逗号分隔）
        5. 输出目录选择区域
        6. 提交按钮
        
        设置各组件的基本属性和占位文本
        """
        self.setWindowTitle("Markdown / PDF 发布助手")
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 1. 文件选择
        file_layout = QHBoxLayout()
        self.btn_open = QPushButton("选择文件")
        self.btn_open.clicked.connect(self._open_file_dialog)
        self.lbl_file = QLabel("未选择文件")
        file_layout.addWidget(self.btn_open)
        file_layout.addWidget(self.lbl_file, 1)
        main_layout.addLayout(file_layout)

        # 2. 标题
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("文章标题")
        main_layout.addWidget(QLabel("标题"))
        main_layout.addWidget(self.edit_title)

        # 3. 描述
        self.edit_desc = QTextEdit()
        self.edit_desc.setMaximumHeight(80)
        self.edit_desc.setPlaceholderText("简要描述")
        main_layout.addWidget(QLabel("描述"))
        main_layout.addWidget(self.edit_desc)

        # 4. 标签（逗号分隔）
        self.edit_tags = QLineEdit()
        self.edit_tags.setPlaceholderText("标签1, 标签2, ...")
        main_layout.addWidget(QLabel("标签（逗号或空格分隔，单个标签内无空格）"))
        main_layout.addWidget(self.edit_tags)

        # 5. 输出目录
        out_layout = QHBoxLayout()
        self.btn_out = QPushButton("选择输出目录")
        self.btn_out.clicked.connect(self._choose_out_dir)
        self.lbl_out = QLabel(self.output_dir())
        out_layout.addWidget(self.btn_out)
        out_layout.addWidget(self.lbl_out, 1)
        main_layout.addLayout(out_layout)

        # 6. 提交
        self.btn_submit = QPushButton("生成文章")
        self.btn_submit.clicked.connect(self._do_submit)
        main_layout.addWidget(self.btn_submit)

    # ---------- 公共接口 ----------
    def prefill_title(self, title: str):
        """
        预填充标题字段（供外部调用）
        
        通常在文件选择后由主应用调用，用于自动填写标题
        
        :param title: 要填充的标题文本
        """
        self.edit_title.setText(title)

    def output_dir(self) -> str:
        """
        获取当前设置的输出目录
        
        :return: 当前输出目录路径
        """
        return self._last_out_dir

    def show_error(self, msg: str):
        """
        显示错误消息对话框
        
        :param msg: 要显示的错误消息
        """
        QMessageBox.critical(self, "错误", msg)

    def show_success(self, msg: str):
        """
        显示成功消息对话框
        
        :param msg: 要显示的成功消息
        """
        QMessageBox.information(self, "成功", msg)

    # ---------- 内部槽 ----------
    def _open_file_dialog(self):
        """
        打开文件选择对话框（内部槽函数）
        
        执行以下操作：
        1. 显示文件选择对话框（限制为.md和.pdf文件）
        2. 更新文件路径标签
        3. 触发 on_file_select 回调
        4. 记住最后选择的目录
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Markdown 或 PDF 文件",
            self._last_file_dir,                # 使用文件记忆目录
            "支持文件 (*.md *.pdf)"
        )
        if file_path:
            self.lbl_file.setText(file_path)
            # 更新文件选择目录为当前文件所在目录
            self._last_file_dir = os.path.dirname(file_path)
            self.settings.setValue("last_file_dir", self._last_file_dir)
            self.on_file_select(file_path)

    def _choose_out_dir(self):
        """
        打开目录选择对话框（内部槽函数）
        
        执行以下操作：
        1. 显示目录选择对话框
        2. 更新输出目录标签
        3. 保存新目录到设置
        """
        new_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self._last_out_dir)   # 使用输出记忆目录
        if new_dir:
            self._last_out_dir = new_dir
            self.lbl_out.setText(new_dir)
            self.settings.setValue("last_out_dir", new_dir)

    def _do_submit(self):
        """
        处理提交操作（内部槽函数）
        
        执行以下操作：
        1. 检查是否已选择文件
        2. 收集表单数据（标题、描述、标签）
        3. 触发 on_submit 回调，传递文件路径和元数据
        """
        file_path = self.lbl_file.text()
        if file_path == "未选择文件":
            self.show_error("请先选择文件")
            return
        meta = {
            'title': self.edit_title.text().strip(),
            'description': self.edit_desc.toPlainText().strip(),
            # 'tags': [t.strip() for t in self.edit_tags.text().split(',') if t.strip()],
            'tags': re.split(r'[,\s，]+', self.edit_tags.text())
        }

        self.on_submit(file_path, meta)
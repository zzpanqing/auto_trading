# PDF 转 TXT 工具使用指南

## 📋 功能介绍

`pdf_to_txt.py` 是一个Python程序，用于**批量提取PDF文件中的文本内容**，并将所有文本合并到一个`.txt`文件中。

### 主要特性
- ✅ 递归扫描文件夹中的所有PDF文件（包括子目录）
- ✅ 自动提取PDF中的文本内容
- ✅ 保留页码信息（标记每页内容）
- ✅ 将所有PDF文本合并到单个txt文件
- ✅ 自动标记每个PDF文件的分隔符
- ✅ 详细的进度显示和错误处理

---

## 🚀 快速开始

### 第一步：安装依赖库

选择以下任意一种方法安装PDF提取库：

#### 方法1：使用 pdfplumber（推荐）
```powershell
pip install pdfplumber
```
**优势**：更现代，文本提取效果更好，支持更多PDF格式。

#### 方法2：使用 PyPDF2
```powershell
pip install PyPDF2
```
**优势**：轻量级，适合简单的PDF提取任务。

---

### 第二步：使用脚本

#### 基本用法 - 提取当前文件夹的PDF
```powershell
python pdf_to_txt.py
```
- 扫描当前目录及子目录的所有PDF文件
- 输出文件为 `extracted_text.txt`

#### 指定PDF文件夹位置
```powershell
python pdf_to_txt.py "C:\Users\YourName\Documents\PDFs"
```
- 扫描指定文件夹中的所有PDF
- 输出文件为 `extracted_text.txt`

#### 指定输出文件名
```powershell
python pdf_to_txt.py "C:\path\to\pdf\folder" "my_custom_output.txt"
```
- 扫描指定文件夹
- 输出文件为 `my_custom_output.txt`

---

## 📖 使用示例

### 示例1：简单用法
```powershell
# 在当前目录运行
cd D:\Documents\PDFs
python pdf_to_txt.py
```
**结果**：
- 找到所有PDF文件
- 提取文本内容
- 生成 `extracted_text.txt`

### 示例2：处理特定文件夹
```powershell
python pdf_to_txt.py "D:\my_research\papers"
```

### 示例3：自定义输出名称
```powershell
python pdf_to_txt.py "D:\reports" "combined_reports.txt"
```

---

## 📝 输出文件格式

生成的`.txt`文件格式如下：

```
============================================================
文件: document1.pdf
============================================================

--- 第 1 页 ---
[第1页的文本内容]

--- 第 2 页 ---
[第2页的文本内容]


============================================================
文件: document2.pdf
============================================================

--- 第 1 页 ---
[第1页的文本内容]
```

**说明**：
- 每个PDF用分隔符 `====` 清晰标记
- 包含PDF文件名
- 每一页都标记了页码
- 页面内容之间有清晰的分隔

---

## ⚙️ 参数说明

### 命令行参数

```
python pdf_to_txt.py [pdf_folder] [output_file]
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `pdf_folder` | 否 | `.` (当前目录) | PDF文件所在的文件夹路径 |
| `output_file` | 否 | `extracted_text.txt` | 输出的txt文件名称 |

### 脚本内部配置

编辑 `pdf_to_txt.py` 中的这一行可以切换提取引擎：

```python
use_pdfplumber = True   # 使用 pdfplumber（推荐）
# use_pdfplumber = False  # 改为 False 时使用 PyPDF2
```

---

## ❌ 常见问题

### Q1：运行时出现 "ModuleNotFoundError"
**原因**：未安装PDF提取库

**解决方案**：
```powershell
pip install pdfplumber
# 或
pip install PyPDF2
```

### Q2：找不到PDF文件
**可能的原因**：
- PDF文件不在指定的文件夹中
- 文件名不是 `.pdf` 后缀

**解决方案**：
- 检查PDF文件路径是否正确
- 确保文件扩展名是小写的 `.pdf`
- 用资源管理器确认文件位置

### Q3：提取的文本为空或乱码
**可能的原因**：
- PDF文件被加密或损坏
- PDF使用了特殊的文字编码

**解决方案**：
- 尝试用另一个PDF提取库（切换 `use_pdfplumber` 参数）
- 检查PDF文件是否能在Adobe Reader中正常打开
- 如果是扫描的PDF（图片型），需要使用OCR技术

### Q4：输出文件很大
**原因**：正常现象，多个PDF文本合并后体积会很大

**建议**：
- 用文本编辑器（如VS Code）打开查看
- 可以分次处理小批量PDF
- 不建议用记事本打开超大文本文件

---

## 🔧 高级用法

### 修改脚本以添加自定义功能

如果需要修改提取逻辑，可以编辑以下函数：

1. **`extract_pdf_text_pdfplumber(pdf_path)`** - 使用pdfplumber提取
2. **`extract_pdf_text_pypdf(pdf_path)`** - 使用PyPDF2提取
3. **`pdf_to_txt(...)`** - 主程序逻辑

例如，要跳过某些PDF文件，可以在主函数中添加过滤条件。

---

## 💡 提示

- **首次使用**：推荐使用 `pdfplumber`，效果更好
- **备份原文件**：处理重要PDF前，备份原文件
- **测试**：先用小批量PDF测试，确认效果满意后再处理大量文件
- **编码**：输出文件统一使用 UTF-8 编码，支持中文和其他语言

---

## 📞 获取帮助

如有问题，可以：
1. 检查本文档的常见问题部分
2. 确认依赖库已正确安装
3. 检查PDF文件是否损坏
4. 查看脚本的错误信息输出

---

**最后更新**：2026-06-04

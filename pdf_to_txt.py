"""
将PDF文件夹中的所有PDF文本内容合并到一个.txt文件
"""
import os
import sys
from pathlib import Path


def extract_pdf_text_pdfplumber(pdf_path):
    """使用 pdfplumber 提取PDF文本"""
    try:
        import pdfplumber
    except ImportError:
        print("❌ pdfplumber 未安装，请运行: pip install pdfplumber")
        return None
    
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- 第 {page_num} 页 ---\n{page_text}"
        return text
    except Exception as e:
        print(f"⚠️  提取失败 {pdf_path}: {e}")
        return None


def extract_pdf_text_pypdf(pdf_path):
    """使用 PyPDF2 提取PDF文本（备选）"""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("❌ PyPDF2 未安装，请运行: pip install PyPDF2")
        return None
    
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- 第 {page_num} 页 ---\n{page_text}"
        return text
    except Exception as e:
        print(f"⚠️  提取失败 {pdf_path}: {e}")
        return None


def pdf_to_txt(pdf_folder, output_file="extracted_text.txt", use_pdfplumber=True):
    """
    将指定文件夹中的所有PDF文本提取到一个txt文件
    
    Args:
        pdf_folder: PDF文件夹路径
        output_file: 输出的txt文件名
        use_pdfplumber: 是否使用pdfplumber（True）或PyPDF2（False）
    """
    pdf_path = Path(pdf_folder)
    
    # 验证文件夹存在
    if not pdf_path.exists():
        print(f"❌ 文件夹不存在: {pdf_folder}")
        return False
    
    if not pdf_path.is_dir():
        print(f"❌ 路径不是文件夹: {pdf_folder}")
        return False
    
    # 查找所有PDF文件
    pdf_files = sorted(pdf_path.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  在 {pdf_folder} 中未找到PDF文件")
        return False
    
    print(f"✅ 找到 {len(pdf_files)} 个PDF文件\n")
    
    # 选择提取方法
    extract_func = extract_pdf_text_pdfplumber if use_pdfplumber else extract_pdf_text_pypdf
    
    all_text = []
    success_count = 0
    
    # 提取每个PDF的文本
    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"[{idx}/{len(pdf_files)}] 处理: {pdf_file.name}")
        
        text = extract_func(str(pdf_file))
        if text:
            # 添加文件名和分隔符
            all_text.append(f"\n\n{'='*60}")
            all_text.append(f"文件: {pdf_file.name}")
            all_text.append(f"{'='*60}")
            all_text.append(text)
            success_count += 1
            print(f"  ✓ 成功")
        else:
            print(f"  ✗ 失败")
    
    # 写入txt文件
    if all_text:
        output_path = pdf_path / output_file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(all_text))
            
            print(f"\n{'='*60}")
            print(f"✅ 成功提取 {success_count}/{len(pdf_files)} 个文件")
            print(f"✅ 结果已保存到: {output_path}")
            print(f"{'='*60}")
            return True
        except Exception as e:
            print(f"❌ 写入文件失败: {e}")
            return False
    else:
        print(f"\n❌ 没有成功提取任何PDF文本")
        return False


if __name__ == "__main__":
    # 默认配置
    pdf_folder = "."  # 当前文件夹
    output_file = "extracted_text.txt"
    
    # 命令行参数支持
    if len(sys.argv) > 1:
        pdf_folder = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    # 选择提取方法（默认使用pdfplumber）
    use_pdfplumber = True
    
    print(f"📂 PDF文件夹: {pdf_folder}")
    print(f"📄 输出文件: {output_file}\n")
    
    pdf_to_txt(pdf_folder, output_file, use_pdfplumber=use_pdfplumber)

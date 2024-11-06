from spire.pdf import PdfDocument

def convert_pdf_to_text(pdf_path, output_path):
    try:
        # 載入 PDF 文件
        pdf_doc = PdfDocument()
        pdf_doc.load_from_file(pdf_path)
        
        # 提取文字
        text = ""
        for page in range(pdf_doc.pages.count):
            text += pdf_doc.pages[page].extract_text()
        
        # 將文字寫入 .txt 檔案
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)
        
        print(f"Successfully converted {pdf_path} to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        pdf_doc.close()

# 使用範例
pdf_path = "競賽資料集/reference/finance/1022.pdf"
output_path = "/opt/fintech_project/spire_output/1022.txt"

convert_pdf_to_text(pdf_path, output_path)
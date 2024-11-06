from spire.pdf import PdfDocument
import os

def convert_pdf_to_text(pdf_path, output_path):
    try:
        # make sure target dir exsists
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # use absolute path
        abs_pdf_path = os.path.abspath(pdf_path)
        if not os.path.exists(abs_pdf_path):
            raise FileNotFoundError(f"PDF file not found: {abs_pdf_path}")

        pdf_doc = PdfDocument()
        pdf_doc.LoadFromFile(str(abs_pdf_path))
        
        text = ""
        for i in range(pdf_doc.Pages.Count):
            text += pdf_doc.Pages[i].ExtractText()
        
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)
        
        print(f"Successfully converted {abs_pdf_path} to {output_path}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

    finally:
        if 'pdf_doc' in locals():
            pdf_doc.Dispose()

if __name__ == "__main__":
    base_dir = "/opt/fintech_project"
    pdf_path = os.path.join(base_dir, "競賽資料集/reference/finance/1022.pdf")
    output_path = os.path.join(base_dir, "spire_output/1022.txt")
    convert_pdf_to_text(pdf_path, output_path)
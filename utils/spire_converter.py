from spire.pdf import PdfDocument
import os
import json

def convert_pdfs_to_text(input_dir, output_dir, progress_file='conversion_progress.json'):
    """
    Convert PDFs to text with progress tracking
    """
    try:
        # Create output directory if needed
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        # Load progress from file
        processed_files = {}
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                processed_files = json.load(f)
            print(f"Loaded progress: {len(processed_files)} files already processed")

        # Get PDF files
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
        if not pdf_files:
            print(f"No PDF files found in {input_dir}")
            return

        # Process files
        total = len(pdf_files)
        for index, pdf_file in enumerate(pdf_files, 1):
            # Skip if already processed
            if pdf_file in processed_files:
                print(f"Skipping {pdf_file} (already processed)")
                continue

            pdf_path = os.path.join(input_dir, pdf_file)
            txt_file = os.path.splitext(pdf_file)[0] + '.txt'
            txt_path = os.path.join(output_dir, txt_file)
            
            print(f"Converting {pdf_file} ({index}/{total})...")
            
            # Convert PDF
            pdf_doc = PdfDocument()
            pdf_doc.LoadFromFile(pdf_path)
            
            text = ""
            for i in range(pdf_doc.Pages.Count):
                text += pdf_doc.Pages[i].ExtractText()
            
            # Save text
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            pdf_doc.Dispose()

            # Update progress
            processed_files[pdf_file] = txt_file
            with open(progress_file, 'w') as f:
                json.dump(processed_files, f, indent=2)
            
            print(f"Saved {txt_file}")

        print("All conversions completed!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Progress is saved even if error occurs
        raise

if __name__ == "__main__":
    input_dir = "/opt/fintech_project/競賽資料集/reference/finance"
    output_dir = "/opt/fintech_project/spire_output"
    
    convert_pdfs_to_text(input_dir, output_dir)
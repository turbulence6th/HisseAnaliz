import sys
from io import StringIO
import os

def extract_text_pdfminer(pdf_path):
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.pdfpage import PDFPage

    output_string = StringIO()
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    
    try:
        with open(pdf_path, 'rb') as fp:
            for page_num, page in enumerate(PDFPage.get_pages(fp)):
                interpreter.process_page(page)
                text = output_string.getvalue()
                print(f"--- Page {page_num+1} ---")
                print(text.strip())
                output_string.seek(0)
                output_string.truncate(0)
    except Exception as e:
        raise e
    finally:
        device.close()
        output_string.close()

def extract_text_pypdf(pdf_path):
    from pypdf import PdfReader
    
    try:
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            print(f"--- Page {page_num+1} ---")
            print(text.strip())
    except Exception as e:
        raise e

def extract_text(pdf_path):
    print(f"--- Extracting from: {pdf_path} ---")
    
    try:
        print("Attempting with pdfminer.six...")
        extract_text_pdfminer(pdf_path)
    except Exception as e_miner:
        print(f"pdfminer.six failed: {e_miner}")
        print("Attempting with pypdf...")
        try:
            extract_text_pypdf(pdf_path)
        except Exception as e_pypdf:
            print(f"pypdf also failed: {e_pypdf}")
            print("Could not extract text from this PDF.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_text.py <pdf_file_path> [pdf_file_path2 ...]")
        sys.exit(1)
        
    for path in sys.argv[1:]:
        if os.path.exists(path):
            extract_text(path)
        else:
            print(f"File not found: {path}")

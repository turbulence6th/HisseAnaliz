import sys

def fix_pdf(input_path, output_path):
    with open(input_path, 'rb') as f:
        content = f.read()
    
    # Find the start of the PDF
    start_index = content.find(b'%PDF-')
    
    if start_index == -1:
        print("Error: %PDF- header not found in the file.")
        return

    print(f"Found PDF header at index: {start_index}")
    
    # Extract the PDF content
    pdf_content = content[start_index:]
    
    with open(output_path, 'wb') as f:
        f.write(pdf_content)
    
    print(f"Fixed PDF saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fix_pdf.py <input_pdf> <output_pdf>")
        sys.exit(1)
    
    fix_pdf(sys.argv[1], sys.argv[2])

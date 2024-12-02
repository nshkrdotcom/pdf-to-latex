# pdf_parser.py

import os
import subprocess
import pytesseract  # Example OCR; consider others like TesseractOCR
from PIL import Image
import fitz  # PyMuPDF for PDF handling


class PDFParser:
    def __init__(self, tesseract_path=None):  # Add tesseract path
        """Initializes the PDFParser.  Set the path to your Tesseract executable if needed."""
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def _rasterize_pdf(self, pdf_path, output_dir):
        """Rasterizes a PDF into images (PNG format)."""
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(os.path.join(output_dir, f"page_{page_num + 1:04d}.png"))
        doc.close()


    def extract_text_from_image(self, image_path):  # Updated
        """Extracts text from a single image using OCR."""
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text
        except Exception as e:  # Handle OCR errors
            print(f"Error during OCR: {e}")
            return ""  # Or raise the exception if you want to stop processing



    def parse_pdf(self, pdf_path, output_dir="exported_images"): # Updated
        """Parses a PDF, rasterizes it, and extracts text from each image."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self._rasterize_pdf(pdf_path, output_dir)
        extracted_text = {}  # Store extracted text by page number

        for filename in sorted(os.listdir(output_dir)):  # Maintain page order
            if filename.endswith(".png"):
                image_path = os.path.join(output_dir, filename)
                page_num = int(filename[5:9])  # Extract page number (assuming naming convention) # Updated
                text = self.extract_text_from_image(image_path)
                extracted_text[page_num] = text

        return extracted_text


# Example usage (in your main pipeline script - run_pipeline.py)
if __name__ == "__main__":
    parser = PDFParser()
    pdf_file = "path/to/your/pdf_file.pdf"  # Replace with your PDF file
    extracted_text = parser.parse_pdf(pdf_file)


    for page_num, text in extracted_text.items():
        print(f"Page {page_num}:\n{text}\n")

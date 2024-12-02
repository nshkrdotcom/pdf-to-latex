# run_pipeline.py

import argparse
import os
from pdf_parser import PDFParser
from structure_analyzer import StructureAnalyzer
from persistence_layer import PersistenceLayer
from latex_generator import LaTeXGenerator

def main():
    parser = argparse.ArgumentParser(description="PDF to LaTeX conversion pipeline.")
    parser.add_argument("input_pdf", help="Path to the input PDF file.")
    parser.add_argument("output_tex", help="Path to the output LaTeX file.")
    # Add other command-line arguments as needed (e.g., database credentials, configuration options)
    args = parser.parse_args()



    # 1. PDF Parsing
    pdf_parser = PDFParser()  # Or initialize with Tesseract path if needed
    extracted_text = pdf_parser.parse_pdf(args.input_pdf)




    # 2. Structure Analysis
    analyzer = StructureAnalyzer()
    structured_data = {}
    for page_num, text in extracted_text.items():
        structured_data[page_num] = analyzer.analyze_text(text)


    # 3. Persistence Layer (Example - adapt to your needs)
    # Get database credentials from environment variables or a configuration file
    pg_conn_str = os.environ.get("PG_CONN_STR")  # Or get from config file
    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_username = os.environ.get("NEO4J_USERNAME")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")



    persistence = PersistenceLayer(pg_conn_str, neo4j_uri, neo4j_username, neo4j_password)
    doc_id = persistence.create_document(os.path.basename(args.input_pdf))


    for page_num, page_data in structured_data.items():
        page_id = persistence.create_page(doc_id, page_num,  width=None, height=None) # Get width and height from PDF metadata
        for i, block_data in enumerate(page_data):
            block_id = persistence.create_block(page_id, block_data["type"], x=None, y=None, width=None, height=None, **block_data) # Add layout info if available
            if i > 0:
                persistence.create_follows_relationship(prev_block_id, block_id) # Assumes blocks are in order
            prev_block_id = block_id # Save previous block ID to create FOLLOWS relationships



    # You'll likely need a more sophisticated approach to reconstructing document structure here!
    document_data_for_latex = structured_data


    # 4. LaTeX Generation
    latex_generator = LaTeXGenerator() # Initialize with your template directory if needed
    latex_code = latex_generator.generate_latex(document_data_for_latex)

    with open(args.output_tex, "w") as tex_file:
        tex_file.write(latex_code)


    persistence.close() #  Important: close connections when done!




if __name__ == "__main__":
    main()

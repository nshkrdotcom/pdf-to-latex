# latex_generator.py

from jinja2 import Environment, FileSystemLoader

class LaTeXGenerator:
    def __init__(self, template_dir="templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_latex(self, document_data):
        """Generates LaTeX code from the structured document data.

        Args:
            document_data (dict): A dictionary containing the structured data for the entire document.
                                 This should be organized by page, then by block.

        Returns:
            str: The generated LaTeX code.
        """

        template = self.env.get_template("main.tex")  # Load your main LaTeX template
        latex_code = template.render(document_data=document_data)
        return latex_code



    def _generate_section(self, section_data):  # Helper function
        if section_data["type"] == "heading":
            return f"\\section*{{{section_data['content']}}}\n"
        elif section_data["type"] == "paragraph":
            return f"{section_data['content']}\n\n"  # Add paragraph with double newline for spacing
        # ... (handle other block types) ...
        return ""  # Default return empty string if type not handled



# Example `templates/main.tex` Jinja2 template:
"""
\documentclass{article}
\\begin{document}

{% for page_num, page_data in document_data.items() %}
    {% for block in page_data %}
        {{ generate_section(block) }}  % Call helper function to generate LaTeX for each block
    {% endfor %}
\\end{document}
"""

# Example usage in your main pipeline:

# ... (get structured data from the persistence layer)
# document_data = {
#     1: [{"type": "heading", "content": "Introduction"}, {"type": "paragraph", "content": "This is the first paragraph."}],
#     2: [{"type": "paragraph", "content": "This is a paragraph on the second page."}]
#     # ... data for other pages ...
# }


# generator = LaTeXGenerator()
# latex_code = generator.generate_latex(document_data)

# # Save or further process the LaTeX code
# with open("output.tex", "w") as f:
#     f.write(latex_code)

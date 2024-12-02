import google.generativeai as genai
import os
import requests
import PIL  # Install with: pip install Pillow
from PIL import Image
from io import BytesIO
import base64
import traceback
import time
import random

def _main_prompt(): 
    return r"""Convert the provided scanned image to LaTeX code, adhering to the following specifications:

0. **Preserve Scanned Order:** The generated LaTeX code must maintain the exact same element order as the original scanned image.  

1. **Ignore Lines:** If the first or second line contains "FIPS 203" or "Module-Lattice-Based Key-Encapsulation Mechanism" (regardless of capitalization), ignore those lines.

2. **Restricted Packages:**  Use *only* these packages if required:  `inputenc`, `amsmath`, `amsfonts`, `amssymb`, `algorithm`, `algpseudocode`, `array`, `booktabs`, `float`, `graphicx`, `caption`, `subcaption`, `listings`, `hyperref`, `enumitem`, `setspace`, `xcolor`, `cite`, `mathtools`, `siunitx`, `longtable`, `multirow`, `rotating`, `wrapfig`, and `verbatim`. Do not include any `\usepackage` statements in the output.

3. **Excluded Tags:** Do not include `\title`, `\author`, `\date`, `\maketitle`, or `\begin{document}`/`\end{document}` tags.

4. **Output Format:** Output *only* the LaTeX code, without any additional text or explanations. Do not include the opening and closing \`\`\`latex markers.

5. **Paragraphs:** Separate each paragraph with a blank line.

6. **Formatting:** Accurately reproduce the text formatting from the image. Use:
    * `\textbf{...}` for bold text.
    * `\textit{...}` for italicized text.
    * `\underline{...}` for underlined text.

7. **Content Inclusion/Exclusion:** Include *all* content from the scan, from the very beginning to the end, except page numbers.  This includes titles, subtitles, introductory paragraphs, as well as all numbered and unnumbered sections, formulas, algorithms, lists, and tables. Do not exclude any text elements. Do not create `\section` or `\subsection` tags if they are not present in the original document.

8. **Multi-Page Element Handling:** If any element (text, formula, table, list, figure, etc.) begins on the scanned image but is clearly a continuation from the previous page:
    * **Placement:**  Insert the continuation at the **very beginning** of the LaTeX output for the current page, *before* any other content on that page.
    * **Representation:** Begin the LaTeX output for the continued element with an ellipsis (...) followed by the partial element.  If the beginning of the element is unclear due to the cut-off, add a comment explaining the uncertainty AND include an ellipsis as a placeholder for the missing content (e.g., `% Table begins mid-row; unable to reconstruct previous page content.\n...`).  Attempt to reconstruct missing portions of tables or formulas if possible, adding a comment to indicate the reconstruction.

9. **Special Symbols and Math:**
    *  Accurately reproduce special symbols and mathematical notation.
    * Use correct LaTeX notation for mathematical sets and number systems (e.g., `\mathbb{B}` for the set of bytes, `\mathbb{Z}` for integers).  Clearly define any non-standard notation.
    * Use the following LaTeX code for specific symbols:
        * `←`: `$\gets$`, `$\leftarrow$`, or `$\longleftarrow$`
        * `→`: `$\to$`, `$\rightarrow$`, or `$\longrightarrow$`
        * `∈`: `$\in$`
        * `∋`: `$\ni$`
        * `≤`: `$\leq$`
    * Convert all math symbols to their corresponding LaTeX glyph code.
    * Convert any remaining Unicode characters to their respective LaTeX glyphs.

10. **Faithful Reproduction:** Ensure all formatting (spacing, line breaks, equation placement) is faithfully reproduced in the LaTeX output.

12. **Section and Subsection Numbering:** 
    * If a section or subsection is unnumbered in the image, do not include a number in the LaTeX output (e.g., use `\section*{Foo}`).
    * If numbered, hardcode the number from the image (e.g., `\section*{4. Auxiliary Algorithms}`).  Do not use automatic numbering.

12. **Formula Numbering:** Hardcode formula numbers from the image using `\tag{}` within the `equation` environment (e.g., `\begin{equation}\tag{4.1} ... \end{equation}`). Do not use automatic numbering.

13. **Algorithm Numbering:** Hardcode algorithm numbers from the image. Do not use automatic numbering.  Ensure that the algorithm number is explicitly present within the algorithm environment (e.g., "Algorithm 1").  Use the `algorithm` environment and related commands (`\caption`, `\label`, `\begin{algorithmic}`, etc.) correctly.

14. **Page Numbers:** Ignore page numbers at the bottom of the scanned image.

15. **Consistent Notation:** Maintain consistent notation throughout the document. Define any non-standard notation.

16. **Output:** Output *only* the raw LaTeX code. Do not include ```latex delimiters.

17. **Section Mapping:** Each scanned section will be converted into one or more LaTeX sections based on its content.  Sections shall be split if they contain different content types (e.g., a paragraph followed by a formula). Use the following rules to map scanned sections to LaTeX structures:

    * **Mixed Content:** If a scanned section contains multiple content types (e.g., text and a formula, a list and an algorithm), create separate LaTeX sections for *each* content type, following the rules above.  Retain the original order of the content.  If a heading applies to the whole mixed-content section, include it only before the first sub-section in LaTeX.

    * **Preamble/Introductory Text (Multi-page):**  If the scan's main body begins with text that is a continuation from a previous page, or if the scan begins with text that is not part of a numbered section (e.g., a title, abstract, general introduction), treat this as one more more separate sections.
        ```latex
        where $s \in \mathbb{B}^*$.
        ```
          
    * **No Heading:**
        ```latex
        This is the paragraph text.  Format with appropriate LaTeX commands.
        ```

    * **With Heading:**
        ```latex
        \section*{Section Heading}
        This is the paragraph text. Format with appropriate LaTeX commands.
        ```

    * **Formula Only:**  If a scanned section contains only mathematical formulas, use the "Mathematical Formula Sections" structure:
        ```latex
        \section*{Mathematical Formula Sections}  % Only if a heading is present in the scanned image
        \begin{equation} \label{eq:1}  % Use appropriate label
        ... % Formula content from the scanned image. Use \tag{} for explicit numbering if present.
        \end{equation}
         % Add more equation environments as needed.
        ```

    * **Algorithm Only:** If a scanned section contains only an algorithm, use the "Algorithm Sections" structure, ensuring to include all comments:
        ```latex
        \setcounter{algorithm}{n} % Replace 'n' with (algorithm number from image - 1). Reset before each algorithm.
        \begin{algorithm}[H]
        \caption{The Algorithm Title}  % Replace with title from image
        \textit{An example sentence that is in italics.}
        \begin{algorithmic}[1]
        \renewcommand{\algorithmicrequire}{\textbf{Input:}}
        \renewcommand{\algorithmicensure}{\textbf{Output:}}
        \Require $x \in \mathbb{R}$, $y \in \mathbb{R}$   \Comment{Lorem Ipsum}
        \Ensure $z \in \mathbb{R}$                        \Comment{Lorem Ipsum}
        \State $z \gets x + y$                            \Comment{Lorem Ipsum}
        \State \textbf{if} $z > 10$ \textbf{then}         \Comment{Lorem Ipsum}
        \State \quad $z \gets z - 10$                     \Comment{Lorem Ipsum}
        \State \textbf{end if}                            \Comment{Lorem Ipsum} 
        \State \Return $z$                                \Comment{Lorem Ipsum} 
        \end{algorithmic} 
        \end{algorithm}
        ```

    * **List Only:** If a scanned section contains only a list, use the "List Item Sections" structure:
        ```latex
        \begin{itemize}[noitemsep,itemsep=5pt,topsep=0pt]  % Adjust itemsep to match image spacing if needed
            \item ... % List items from the scanned image
        \end{itemize}
        ```
    * **Table Only:** If a scanned section contains only a table, use the "Tabular Data Sections" structure:
        ```latex
        \section*{Tabular Data Sections}  % Only if a heading is present in the scanned image
        \begin{table}[h]
        \centering
        \begin{tabular}{...}  % Define columns based on the table structure in the image
        ...  % Table data from the image. Use booktabs rules (\toprule, \midrule, \bottomrule) if the table uses horizontal lines.
        \end{tabular}
        \caption{Table Caption} % Replace with caption from the image.
        \label{...}  % Include label from the image (if any).
        \end{table}
        ```

19. **Final Output:** The final output should contain *only* the generated LaTeX code, as described above, without any additional text, diagrams, comments, or other elements not present in the scanned image (except for the required structural elements and formatting commands).
"""

def _preamble():
    return r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{array}
\usepackage{booktabs}
\usepackage{float}
\usepackage{graphicx}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{listings}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{setspace}
\usepackage{xcolor}
\usepackage{cite}
\usepackage{mathtools}
\usepackage{siunitx}
\usepackage{longtable}
\usepackage{multirow}
\usepackage{rotating}
\usepackage{wrapfig}
\usepackage{verbatim}

\usepackage[margin=0.5in]{geometry}
 %top=1in, bottom=1.2in, left=1.5in, right=1in: For individual margin control.
 %a4paper, margin=1in: If you want to explicitly set the paper size as well.
 
\usepackage{blindtext}
\usepackage[skip=10pt plus1pt, indent=40pt]{parskip} 
% \blindtext[1]\par % Use \par to force a new paragraph
% \blindtext[1] 
 
\newlength\tindent
\setlength{\tindent}{\parindent}
\setlength{\parindent}{0pt}
\renewcommand{\indent}{\hspace*{\tindent}}
 
\title{FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard}
\author{}
\date{}

\begin{document}

\maketitle

"""

def _retry():
    return r"""Review the text attached to the end of this prompt, 
which is denoted by the identifier `ORIGINAL_LATEX`. Then follow 
the instructions:

"""

def _oldLaTeX():
    return r""" ORIGINAL_LATEX:
```
"""

def image_to_LaTeX(model, image_path, original_latex=""):
    """Converts an image to LaTeX using the Gemini API."""
    try:
        image_loaded = PIL.Image.open(image_path)
        prompt = _main_prompt()
        if (original_latex != ""):
            retry_text = _retry()
            old_latex = _oldLaTeX()
            prompt = retry_text + prompt + old_latex + original_latex + "```"            
        response = model.generate_content([prompt, image_loaded])
        return response.text

    except requests.exceptions.RequestException as e:
        print(f"Error with Gemini API request: {e}")
        return None
    except FileNotFoundError:
        print(f"Image file not found: {image_path}")
        return None
    except Exception as e:  # Catch any other errors
        traceback.print_exc()
        print(f"An unexpected error occurred: {e}")
        return None

def wrap_LaTeX(LaTeX_content):
    """Wraps the LaTeX content in a complete document."""
    LaTeX_preamble = _preamble()
    LaTeX_postamble = r"""

\end{document}"""
    return LaTeX_preamble + LaTeX_content + LaTeX_postamble

# def money_generate_content(image_list):
    # """Loads images and returns them as a list of PIL Image objects."""
    # loaded_images = []
    # for image_path in image_list:
        # try:
            # image = PIL.Image.open(image_path)
            # loaded_images.append(image)
        # except requests.exceptions.RequestException as e:
            # print(f"Error with Gemini API request: {e}")
            # return None
        # except FileNotFoundError:
            # print(f"Image file not found: {image_path}")
            # return None
        # except Exception as e:  # Catch any other errors
            # traceback.print_exc()
            # print(f"An unexpected error occurred: {e}")
            # return None    
    # return loaded_images

def call_gemini_api(prompt, images, model):
    """Calls the Gemini API with prompt and images. Returns the response text."""
    api_input = [prompt] + images
    response = model.generate_content(api_input)
    return response.text

def _fetch_range(start_page, end_page, model):
    try_again = 0
    for i in range(start_page, end_page):
        if (i < 10):
            i = "0" + str(i)
        image_file = f"exported_images/nistPages-{i}.png"
        tex_file = f"rendered_LaTeX/nistPages-{i}.tex"
        tex_file_part = f"rendered_LaTeX/_nistPages-{i}-a.tex"
        tex_file_part_2 = f"rendered_LaTeX/_nistPages-{i}-b.tex"
        print(f"Loaded image {image_file}")
        LaTeX_content = image_to_LaTeX(model, image_file)
        if LaTeX_content:
            print(f"First pass done.")
            if (try_again != 0):                
                print(f"Double checking...")
                LaTeX_content_2 = image_to_LaTeX(model, image_file, LaTeX_content)
                full_LaTeX = wrap_LaTeX(LaTeX_content_2)
            else:
                full_LaTeX = wrap_LaTeX(LaTeX_content)
            with open(tex_file, "w") as f:
                f.write(full_LaTeX)
            print(f"LaTeX generated for {image_file} and saved to {tex_file}")
            with open(tex_file_part, "w") as f:
                f.write(LaTeX_content)
            print(f"LaTeX generated for {image_file} and saved to {tex_file_part}")
            if (try_again != 0):
                with open(tex_file_part_2, "w") as f:
                    f.write(LaTeX_content_2)
                print(f"LaTeX generated for {image_file} and saved to {tex_file_part_2}")
        sleep_time = random.randint(3,6)
        time.sleep(sleep_time)

def _all_parts_LaTeX(start_page, end_page):
    out = ""
    print("Combining the saved fragments into a single .tex file.")
    for i in range(start_page, end_page):
        if (i < 10):
            i = "0" + str(i)
        tex_file_part = f"rendered_LaTeX/_nistPages-{i}-a.tex"
        with open(tex_file_part, 'r') as file:
            out = out + file.read()
        continue
    allParts = out
    full = wrap_LaTeX(allParts)
    tex_file = "rendered_LaTeX/FULL_NIST_TEX.tex";
    with open(tex_file, "w") as f:
        f.write(full)

    
if __name__ == "__main__":
    os.environ["GRPC_VERBOSITY"] = "ERROR"
    os.environ["GLOG_minloglevel"] = "2"
    key=os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    start_page = 17
    end_page = 18
    _fetch_range(start_page, end_page, model)
    #_all_parts_LaTeX(start_page, end_page)
    

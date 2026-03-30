# gen-pdf

Generate the PDF from the literate noweb document.

## Instructions

Run these commands from the project root.

If any of these steps fail, stop and inform the user.

1. Ensure the output directory exists: `mkdir -p output`
2. Tangle: `python weave.py main.nw output`
3. Copy support files: `cp noweb.sty output/ && cp -r images output/`
4. Generate font_data.tex: `python font_data.py 83A5 92A4 output/font_data.tex`
5. Generate mob_font_data.tex: `python mob_font_data.py`
6. Run pdflatex once: `cd output && pdflatex main.tex`
7. Run pdflatex again (to resolve references): `pdflatex main.tex`

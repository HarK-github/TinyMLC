import sys
import subprocess
import pathlib

def compile_pdf(tex_file):
    base = tex_file.replace('.tex', '')
    cmd = ['pdflatex', '-interaction=nonstopmode', tex_file]
    # run twice for cross references and page numbering
    subprocess.run(cmd, capture_output=True, text=True)
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    # clean aux files
    for ext in ['.aux', '.log', '.out', '.toc']:
        p = pathlib.Path(f'{base}{ext}')
        if p.exists():
            p.unlink()
            
    pdf_file = f'{base}.pdf'
    if pathlib.Path(pdf_file).exists():
        info = subprocess.run(['pdfinfo', pdf_file], capture_output=True, text=True)
        for line in info.stdout.splitlines():
            if 'Pages:' in line:
                return int(line.split(':')[1].strip())
    return None

if __name__ == '__main__':
    print("Variant builder ready.")

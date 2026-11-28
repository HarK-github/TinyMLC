import sys, subprocess, pathlib

def compile_and_count(filename):
    res = subprocess.run(["pdflatex", "-interaction=nonstopmode", filename], capture_output=True, text=True)
    base = filename.replace(".tex", "")
    for ext in [".aux", ".log", ".out", ".toc"]:
        p = pathlib.Path(f"{base}{ext}")
        if p.exists(): p.unlink()
    
    info = subprocess.run(["pdfinfo", f"{base}.pdf"], capture_output=True, text=True)
    for line in info.stdout.splitlines():
        if "Pages:" in line:
            return int(line.split(":")[1].strip())
    return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Pages:", compile_and_count(sys.argv[1]))

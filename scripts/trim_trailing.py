from pathlib import Path

p = Path("longform_builder.py")
s = p.read_text(encoding="utf-8").splitlines()
# remove trailing empty lines
while s and s[-1].strip() == "":
    s.pop()
p.write_text("\n".join(s) + "\n", encoding="utf-8")
print("trimmed")
for fname in ["youtube.py"]:
    p = Path(fname)
    if p.exists():
        s = p.read_text(encoding="utf-8").splitlines()
        while s and s[-1].strip() == "":
            s.pop()
        p.write_text("\n".join(s) + "\n", encoding="utf-8")
        print(f"trimmed {fname}")

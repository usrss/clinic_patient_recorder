"""Extract text from docx template files."""
import zipfile, xml.etree.ElementTree as ET, os, json

template_dir = "certificates/medical_certs_template"
W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def extract_text(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    paras = []
    for p in root.iter(W_NS + 'p'):
        texts = [t.text or '' for t in p.iter(W_NS + 't')]
        line = ''.join(texts).strip()
        if line:
            paras.append(line)
    return paras

results = {}
for fname in sorted(os.listdir(template_dir)):
    if fname.endswith('.docx'):
        path = os.path.join(template_dir, fname)
        results[fname] = extract_text(path)

# Write to a JSON file
with open('docx_extracted.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Also print to stdout for visibility
for fname, lines in results.items():
    print(f"\n{'='*60}")
    print(f"  {fname}")
    print(f"{'='*60}")
    for line in lines:
        print(f"  {line}")
    print()

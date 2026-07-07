"""Extract all text from the three docx template files."""
import zipfile
import json
import xml.etree.ElementTree as ET

def extract_paragraphs(docx_path):
    """Extract text with paragraph breaks from a docx file."""
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read('word/document.xml')
            root = ET.fromstring(xml_content)
        
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        paragraphs = []
        for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            para_texts = []
            for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if t.text:
                    para_texts.append(t.text)
            if para_texts:
                paragraphs.append(''.join(para_texts))
        
        return '\n\n'.join(paragraphs)
    except Exception as e:
        return f"ERROR: {e}"

templates = {
    'absences': 'certificates/medical_certs_template/Medical Certificate-Absences  of classes-work.docx',
    'ojt': 'certificates/medical_certs_template/Medical Certificate-OJT.docx',
    'activities': 'certificates/medical_certs_template/Medical Certificate_Activitiest-training-seminars.docx',
}

results = {}
for name, path in templates.items():
    results[name] = extract_paragraphs(path)

with open('docx_text_output.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Also print to stdout
for name, text in results.items():
    print(f"\n{'='*80}")
    print(f"FILE: {name}")
    print(f"{'='*80}")
    print(text)

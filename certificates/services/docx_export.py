import logging
import re
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

from django.conf import settings
from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(settings.BASE_DIR) / "certificates" / "medical_certs_template"

TEMPLATE_MAP = {
    "absences": "Medical Certificate-Absences  of classes-work.docx",
    "ojt": "Medical Certificate-OJT.docx",
    "activities": "Medical Certificate_Activitiest-training-seminars.docx",
}

# ── Jinja / Docx placeholder to form-field mapping ──────────────────────
# These are the only form fields that the current .docx templates actually
# reference. All other fields in the CertificateDetailsForm are not needed
# by any of the docx templates and should be hidden from the wizard form.
#
# Map: certificate_type → set of form field names required by the .docx template
DOCX_FIELD_MAP = {
    'absences': {'diagnosis', 'remarks'},
    'ojt': {'activity_name', 'remarks'},
    'activities': {'activity_name', 'remarks'},
}


def get_docx_placeholders(certificate_type):
    """
    Parse the .docx template file for the given certificate type and extract
    all {{ placeholder }} tokens used within it.

    Returns a set of placeholder names (e.g. {'patient_name', 'diagnosis', 'remarks'}).
    Falls back to a pre-computed mapping if the file cannot be read (e.g. disk
    unavailable in tests or during initial deploy).
    """
    filename = TEMPLATE_MAP.get(certificate_type)
    if not filename:
        return set()

    template_path = TEMPLATE_DIR / filename
    if not template_path.exists():
        # Fallback: use the known field map
        return DOCX_FIELD_MAP.get(certificate_type, set())

    try:
        with zipfile.ZipFile(str(template_path)) as z:
            xml_content = z.read('word/document.xml')
            root = ET.fromstring(xml_content)

        all_text = []
        for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t.text:
                all_text.append(t.text)

        full_text = ' '.join(all_text)
        # Extract {{ placeholder }} and {% if %} tokens
        placeholders = set(re.findall(r'\{\{\s*(\w+)\s*\}\}|\{%\s*if\s+(\w+)', full_text))
        # Flatten: the regex returns tuples, extract whichever group matched
        result = set()
        for match in placeholders:
            result.add(match[0] or match[1])
        return result
    except Exception as exc:
        logger.warning("Could not parse docx template %s: %s", filename, exc)
        return DOCX_FIELD_MAP.get(certificate_type, set())


class CertificateDocxError(Exception):
    pass


def generate_certificate_docx_bytes(certificate) -> bytes:
    """Generate a .docx for the given certificate, returning raw bytes.

    Uses the docxtpl template mapped by certificate type,
    renders with the certificate's placeholder map, and returns
    the .docx as a byte string.
    """
    ct = certificate.certificate_type
    filename = TEMPLATE_MAP.get(ct)
    if not filename:
        raise CertificateDocxError(f"No .docx template mapped for type '{ct}'")

    template_path = TEMPLATE_DIR / filename
    if not template_path.exists():
        raise CertificateDocxError(f"Template file missing on disk: {template_path}")

    context = certificate._build_placeholder_map()

    try:
        doc = DocxTemplate(str(template_path))
        doc.render(context)
    except Exception as exc:
        logger.exception("Failed rendering certificate #%s to docx", certificate.pk)
        raise CertificateDocxError(f"Could not render certificate: {exc}") from exc

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

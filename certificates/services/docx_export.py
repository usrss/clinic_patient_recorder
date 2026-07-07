import logging
from io import BytesIO
from pathlib import Path

from django.conf import settings
from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(settings.BASE_DIR) / "certificates" / "medical_certs_template"

TEMPLATE_MAP = {
    "standard": "Medical Certificate-Absences  of classes-work.docx",
    "dental": "Medical Certificate-Absences  of classes-work.docx",
    "fit_to_work": "Medical Certificate-OJT.docx",
    "fit_to_play": "Medical Certificate_Activitiest-training-seminars.docx",
}


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

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class CertificatePdfError(Exception):
    pass


# ── Locate soffice on Windows ──────────────────────────────────────────────
_LIBREOFFICE_CANDIDATES = [
    # Standard install paths on Windows
    "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
]


def _find_soffice() -> str:
    """Return the path to the soffice executable.

    Checks common install locations first, then falls back to ``soffice``
    on the system PATH (works on Linux/macOS and Windows with PATH set).
    """
    for candidate in _LIBREOFFICE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    on_path = shutil.which("soffice")
    if on_path:
        return on_path
    # Final fallback — let subprocess raise a clear error
    return "soffice"


_SOFFICE_PATH = _find_soffice()
logger.info("Using LibreOffice at: %s", _SOFFICE_PATH)


def convert_docx_bytes_to_pdf(docx_bytes: bytes) -> bytes:
    """Convert a .docx byte string to PDF via headless LibreOffice.

    Writes the .docx to a temporary directory, invokes ``soffice --headless
    --convert-to pdf``, reads back the resulting PDF bytes, and cleans up.

    .. warning::
       Headless ``soffice`` instances can conflict under concurrent load.
       For production, consider a lock, a process pool, or queuing conversion
       to a background worker.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        docx_path = tmp_path / "certificate.docx"
        docx_path.write_bytes(docx_bytes)

        try:
            result = subprocess.run(
                [
                    _SOFFICE_PATH, "--headless", "--norestore",
                    "--convert-to", "pdf", "--outdir", str(tmp_path),
                    str(docx_path),
                ],
                capture_output=True,
                timeout=60,
                check=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            logger.exception("LibreOffice conversion failed: %s", exc)
            raise CertificatePdfError("PDF conversion failed") from exc

        pdf_path = tmp_path / "certificate.pdf"
        if not pdf_path.exists():
            logger.error(
                "LibreOffice did not produce a PDF. stdout=%s stderr=%s",
                result.stdout, result.stderr,
            )
            raise CertificatePdfError("PDF conversion did not produce output")

        return pdf_path.read_bytes()

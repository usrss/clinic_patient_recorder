import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class CertificatePdfError(Exception):
    pass


# ── Locate soffice binary ──────────────────────────────────────────────────
# On Linux/macOS (including Docker), ``shutil.which("soffice")`` finds
# the binary on PATH. On Windows fall back to common install locations.
_WINDOWS_SOFFICE_CANDIDATES = [
    "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
]


def _find_soffice() -> str:
    """Return the path to the soffice executable."""
    # 1. Try PATH first (works on Linux/macOS/Docker, also on Windows with PATH set)
    on_path = shutil.which("soffice")
    if on_path:
        return on_path
    # 2. Fall back to common Windows install paths
    for candidate in _WINDOWS_SOFFICE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    # 3. Let subprocess raise a clear FileNotFoundError
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
            # Point the LibreOffice user profile to a temp dir so it doesn't
            # try to write to ~/.config/libreoffice (which may fail in Docker).
            profile_dir = tmp_path / "libreoffice-profile"
            profile_dir.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                [
                    _SOFFICE_PATH, "--headless", "--norestore", "--nofirststartwizard",
                    "-env:UserInstallation=file://" + str(profile_dir).replace("\\", "/"),
                    "--convert-to", "pdf", "--outdir", str(tmp_path),
                    str(docx_path),
                ],
                capture_output=True,
                timeout=120,
                check=True,
            )
        except FileNotFoundError:
            raise CertificatePdfError(
                "LibreOffice (soffice) is not installed or not found on PATH. "
                "Install it or check the Dockerfile."
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

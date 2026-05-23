from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docling.backend.msword_backend import MsWordDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument


def extract_document_text(content: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix != ".docx":
        return ""
    input_document = InputDocument(
        path_or_stream=BytesIO(content),
        format=InputFormat.DOCX,
        backend=MsWordDocumentBackend,
        filename=filename,
    )
    return input_document._backend.convert().export_to_markdown().strip()

"""
Contract Document Parser.
Extracts structured clauses from .docx, .pdf, and raw text representations.
"""

import re
from pathlib import Path
from typing import List, Union
import docx
from pypdf import PdfReader

from .models import ContractClause


class ContractParser:
    """
    Parses Russian commercial supply agreements, extracting numbered clauses.
    """

    CLAUSE_PATTERN = re.compile(r"^(?:п\.|пп\.|статья\s+)?(\d+(?:\.\d+)+)\.?\s*(.*)", re.IGNORECASE)

    @classmethod
    def from_docx(cls, file_path: Union[str, Path]) -> List[ContractClause]:
        """Extracts numbered clauses from Microsoft Word (.docx) document."""
        doc = docx.Document(str(file_path))
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return cls.from_text(full_text)

    @classmethod
    def from_pdf(cls, file_path: Union[str, Path]) -> List[ContractClause]:
        """Extracts numbered clauses from PDF document."""
        reader = PdfReader(str(file_path))
        text_parts = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
        return cls.from_text("\n".join(text_parts))

    @classmethod
    def from_text(cls, text: str) -> List[ContractClause]:
        """
        Segments raw contract text into individual ContractClause objects.
        """
        clauses: List[ContractClause] = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        current_clause_id = "Преамбула"
        current_text_buf: List[str] = []

        for line in lines:
            match = cls.CLAUSE_PATTERN.match(line)
            if match:
                if current_text_buf:
                    clauses.append(ContractClause(
                        clause_id=current_clause_id,
                        text=" ".join(current_text_buf)
                    ))
                    current_text_buf = []

                current_clause_id = match.group(1)
                remainder = match.group(2)
                if remainder:
                    current_text_buf.append(remainder)
            else:
                current_text_buf.append(line)

        if current_text_buf:
            clauses.append(ContractClause(
                clause_id=current_clause_id,
                text=" ".join(current_text_buf)
            ))

        return clauses

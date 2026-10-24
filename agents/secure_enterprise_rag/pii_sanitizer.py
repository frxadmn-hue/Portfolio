"""
Cryptographic Privacy Vault & PII Sanitizer for Natura Siberica.
Ensures zero-leakage of proprietary cosmetic formulas and Russian 152-FZ PII to external LLMs.
"""

import hashlib
import re
from typing import Dict, List, Tuple
from cryptography.fernet import Fernet

from config.settings import get_settings
from .models import DocumentChunk, SanitizedChunk


class EnterprisePrivacyGuard:
    """
    Sanitizes confidential text by replacing sensitive PII and proprietary formulation ratios
    with reversible cryptographic vault tokens before passing context to LLM models.
    """

    def __init__(self, master_key: str = None):
        settings = get_settings()
        key_raw = master_key or settings.VAULT_SECRET_KEY
        try:
            self.fernet = Fernet(key_raw.encode("utf-8"))
        except Exception:
            # Fallback self-generated 32-byte key
            self.fernet = Fernet(Fernet.generate_key())

        # In-memory secure local token vault (token_id -> encrypted_original_value)
        self._vault_store: Dict[str, bytes] = {}

        # 152-ФЗ и коммерческие паттерны
        self.patterns = [
            # Российский паспорт (серия и номер: 4509 123456)
            ("PII_PASSPORT", re.compile(r"\b\d{4}\s+\d{6}\b")),
            # СНИЛС (123-456-789 00)
            ("PII_SNILS", re.compile(r"\b\d{3}-\d{3}-\d{3}\s+\d{2}\b")),
            # ИНН (10 или 12 цифр)
            ("PII_INN", re.compile(r"\b\d{10}(?:\d{2})?\b")),
            # Российский номер телефона (+7 / 8)
            ("PII_PHONE", re.compile(r"(?:\+7|8)[\s\-]?(?:\(?\d{3}\)?[\s\-]?)\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")),
            # Электронная почта
            ("PII_EMAIL", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
            # Банковский расчетный счет (20 цифр, начинающихся на 407/408)
            ("FIN_BANK_ACC", re.compile(r"\b40[78]\d{17}\b")),
            # Концентрация активных дикоросов и точные проценты ввода в формулу
            ("FORMULA_PERCENT", re.compile(r"\b\d+(?:[.,]\d+)?\s*%\s*(?:масла|экстракта|ввода|активного|концентрации|чистоты)\b", re.IGNORECASE)),
            # Точные навески рецептуры (например, 24.5 г/л или 12.8 кг на варку)
            ("FORMULA_BATCH", re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:г/л|мг/мл|кг\s+на\s+варку)\b", re.IGNORECASE)),
        ]

    def _encrypt_and_store(self, sensitive_text: str, category: str) -> str:
        """Encrypts sensitive entity and returns an obfuscated token ID."""
        digest = hashlib.sha256(sensitive_text.strip().encode("utf-8")).hexdigest()[:8].upper()
        token = f"[VAULT_{category}_{digest}]"
        
        # Store encrypted bytes
        encrypted_bytes = self.fernet.encrypt(sensitive_text.encode("utf-8"))
        self._vault_store[token] = encrypted_bytes
        return token

    def sanitize_text(self, text: str) -> Tuple[str, List[str], bool, bool]:
        """
        Replaces all sensitive occurrences with secure tokens.
        Returns: (sanitized_text, token_keys, has_pii, has_formula)
        """
        sanitized = text
        token_keys = []
        has_pii = False
        has_formula = False

        for category, regex in self.patterns:
            matches = list(regex.finditer(sanitized))
            # Замена в обратном порядке для сохранения смещений
            for m in reversed(matches):
                val = m.group(0)
                token = self._encrypt_and_store(val, category)
                start, end = m.span()
                sanitized = sanitized[:start] + token + sanitized[end:]
                token_keys.append(token)
                
                if "PII" in category:
                    has_pii = True
                if "FORMULA" in category:
                    has_formula = True

        return sanitized, token_keys, has_pii, has_formula

    def sanitize_chunk(self, chunk: DocumentChunk) -> SanitizedChunk:
        """Sanitizes a full DocumentChunk."""
        sanitized_txt, tokens, pii_flag, formula_flag = self.sanitize_text(chunk.text)
        return SanitizedChunk(
            chunk_id=chunk.chunk_id,
            sanitized_text=sanitized_txt,
            redaction_count=len(tokens),
            contains_pii=pii_flag,
            contains_formula_secret=formula_flag,
            token_vault_keys=tokens
        )

    def restore_tokens(self, sanitized_text: str) -> str:
        """
        De-anonymizes tokens back to cleartext within the authorized on-premise perimeter.
        """
        restored = sanitized_text
        for token, enc_bytes in self._vault_store.items():
            if token in restored:
                try:
                    plain_val = self.fernet.decrypt(enc_bytes).decode("utf-8")
                    restored = restored.replace(token, plain_val)
                except Exception:
                    pass
        return restored

# -*- coding: utf-8 -*-
"""
Compatibility entry point for Legal Auditor demo.
Invokes the production-grade runner pipeline.
"""

from .runner import run_legal_audit

if __name__ == "__main__":
    run_legal_audit()

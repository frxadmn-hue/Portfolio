# -*- coding: utf-8 -*-
"""
Compatibility entry point for Secure RAG demo.
Invokes the production-grade runner pipeline.
"""

from .runner import run_privacy_guard_demo

if __name__ == "__main__":
    run_privacy_guard_demo()

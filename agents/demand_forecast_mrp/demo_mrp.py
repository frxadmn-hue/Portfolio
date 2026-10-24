# -*- coding: utf-8 -*-
"""
Compatibility entry point for MRP Agent demo.
Invokes the production-grade runner pipeline.
"""

from .runner import run_pipeline

if __name__ == "__main__":
    run_pipeline()

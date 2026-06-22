"""Tests for the public db_tools API surface."""

import subprocess
import sys


def test_import_db_tools_does_not_load_sqlalchemy():
    """Importing db_tools for config helpers should not load sqlalchemy."""
    code = "import db_tools; import sys; assert 'sqlalchemy' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)


def test_setup_openssl_legacy_exported():
    """setup_openssl_legacy must be importable from the package root."""
    from db_tools import setup_openssl_legacy

    assert callable(setup_openssl_legacy)

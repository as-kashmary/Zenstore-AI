"""
Shared pytest fixtures.
Full async DB + auth fixtures will be added in feature/testing-and-hardening.
"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the async backend for pytest-asyncio."""
    return "asyncio"
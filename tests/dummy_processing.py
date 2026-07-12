"""Dummy processing function for standalone tests."""

from typing import Any


def dummy_processing(job_pk: int, **kwargs: Any) -> None:
    """No-op processing function for test scheduling."""

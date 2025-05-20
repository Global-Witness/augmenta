"""Tests for core augmenta functionality."""

import pytest
from augmenta.augmenta import ProcessingResult


def test_processing_result_creation():
    """Test that ProcessingResult instances can be created with expected values."""
    # Test with minimal args
    result = ProcessingResult(index=1, data={"test": "value"})
    assert result.index == 1
    assert result.data == {"test": "value"}
    assert result.error is None

    # Test with all args
    result_with_error = ProcessingResult(
        index=2,
        data=None,
        error="Test error message"
    )
    assert result_with_error.index == 2
    assert result_with_error.data is None
    assert result_with_error.error == "Test error message"
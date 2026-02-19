"""Unit tests for PySpark quality checks."""
import pytest
from unittest.mock import MagicMock
from src.quality.spark_checks import CheckStatus, QualityResult


class TestQualityResult:
    def test_pass_status(self):
        r = QualityResult("test", "bronze", "suits", 100, 97, 3, 97.0, 95.0, CheckStatus.PASS)
        assert r.status == CheckStatus.PASS

    def test_fail_status(self):
        r = QualityResult("test", "bronze", "suits", 100, 70, 30, 70.0, 95.0, CheckStatus.FAIL)
        assert r.status == CheckStatus.FAIL

    def test_pass_rate_calculation(self):
        r = QualityResult("test", "silver", "suits", 200, 190, 10, 95.0, 95.0, CheckStatus.PASS)
        assert r.pass_rate == 95.0

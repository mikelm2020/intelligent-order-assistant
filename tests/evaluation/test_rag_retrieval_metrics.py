import pytest

from tests.evaluation.rag_retrieval_metrics import (
    calculate_retrieval_metrics,
)


def test_calculate_retrieval_metrics():
    metrics = calculate_retrieval_metrics([True, True, True, True, False])

    assert metrics.total_cases == 5
    assert metrics.correct_cases == 4
    assert metrics.accuracy == pytest.approx(0.8)


def test_calculate_retrieval_metrics_with_all_correct():
    metrics = calculate_retrieval_metrics([True, True, True, True, True])

    assert metrics.total_cases == 5
    assert metrics.correct_cases == 5
    assert metrics.accuracy == pytest.approx(1.0)


def test_calculate_retrieval_metrics_with_no_cases():
    metrics = calculate_retrieval_metrics([])

    assert metrics.total_cases == 0
    assert metrics.correct_cases == 0
    assert metrics.accuracy == 0.0


def test_rag_retrieval_evaluation_metrics():
    results = [
        True,
        True,
        True,
        True,
        True,
    ]

    metrics = calculate_retrieval_metrics(results)

    assert metrics.total_cases == 5
    assert metrics.correct_cases == 5
    assert metrics.accuracy == pytest.approx(1.0)

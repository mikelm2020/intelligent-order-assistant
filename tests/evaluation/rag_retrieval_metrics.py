from dataclasses import dataclass


@dataclass
class RetrievalMetrics:
    total_cases: int
    correct_cases: int

    @property
    def accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return self.correct_cases / self.total_cases


def calculate_retrieval_metrics(
    results: list[bool],
) -> RetrievalMetrics:
    return RetrievalMetrics(
        total_cases=len(results),
        correct_cases=sum(results),
    )

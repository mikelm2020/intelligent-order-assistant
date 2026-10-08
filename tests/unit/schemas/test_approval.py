import pytest
from pydantic import ValidationError

from app.schemas.rag import ApprovalDecision


@pytest.mark.parametrize("value", ["true", "false", 0, 1, None])
def test_approval_requires_actual_boolean(value):
    with pytest.raises(ValidationError):
        ApprovalDecision(approve=value)

import pytest
from src.domain.value_objects.work_item_id import WorkItemId

class TestWorkItemId:
    def test_valid_id(self):
        wi_id = WorkItemId(12345)
        assert wi_id.value == 12345
        assert str(wi_id) == "12345"
        assert int(wi_id) == 12345

    def test_invalid_type(self):
        with pytest.raises(TypeError):
            WorkItemId("12345")

    def test_negative_id(self):
        with pytest.raises(ValueError, match="must be positive"):
            WorkItemId(-1)

    def test_zero_id(self):
        with pytest.raises(ValueError, match="must be positive"):
            WorkItemId(0)

    def test_too_large_id(self):
        with pytest.raises(ValueError, match="too large"):
            WorkItemId(1000000)

    def test_from_string_valid(self):
        wi_id = WorkItemId.from_string("12345")
        assert wi_id is not None
        assert wi_id.value == 12345

    def test_from_string_invalid(self):
        assert WorkItemId.from_string("abc") is None
        assert WorkItemId.from_string("") is None

    def test_format_for_ado(self):
        wi_id = WorkItemId(123)
        assert wi_id.format_for_ado() == "123"

    def test_format_for_display(self):
        wi_id = WorkItemId(123)
        assert wi_id.format_for_display() == "#123"

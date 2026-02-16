import pytest
from datetime import timedelta
from src.domain.value_objects.duration import Duration

class TestDuration:
    def test_from_seconds(self):
        d = Duration.from_seconds(3600)
        assert d.seconds == 3600
        assert d.hours == 1.0
        assert d.minutes == 60.0

    def test_from_minutes(self):
        d = Duration.from_minutes(90)
        assert d.seconds == 5400
        assert d.minutes == 90.0
        assert d.hours == 1.5

    def test_from_hours(self):
        d = Duration.from_hours(2)
        assert d.seconds == 7200
        assert d.hours == 2.0

    def test_from_timedelta(self):
        td = timedelta(hours=1, minutes=30)
        d = Duration.from_timedelta(td)
        assert d.seconds == 5400

    def test_from_iso8601(self):
        assert Duration.from_iso8601("PT1H").seconds == 3600
        assert Duration.from_iso8601("PT30M").seconds == 1800
        assert Duration.from_iso8601("PT1H30M").seconds == 5400
        assert Duration.from_iso8601("PT5S").seconds == 5

    def test_invalid_iso8601(self):
        with pytest.raises(ValueError):
            Duration.from_iso8601("invalid")

    def test_negative_duration(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            Duration.from_seconds(-1)

    def test_format_human_readable(self):
        assert Duration.from_hours(2.5).format_human_readable() == "2h 30m"
        assert Duration.from_minutes(45).format_human_readable() == "45m"
        assert Duration.from_hours(1).format_human_readable() == "1h"
        assert Duration.from_seconds(0).format_human_readable() == "0m"

    def test_addition(self):
        d1 = Duration.from_hours(1)
        d2 = Duration.from_hours(2)
        result = d1 + d2
        assert result.hours == 3

    def test_subtraction(self):
        d1 = Duration.from_hours(5)
        d2 = Duration.from_hours(2)
        result = d1 - d2
        assert result.hours == 3

    def test_subtraction_negative_result(self):
        d1 = Duration.from_hours(1)
        d2 = Duration.from_hours(2)
        with pytest.raises(ValueError, match="negative duration"):
            d1 - d2

import re


class Duration:
    """textX custom class for Duration common rule.

    The grammar assigns the regex match to the `raw` attribute.
    We parse it to extract value and unit, and provide to_seconds().
    """

    _PATTERN = re.compile(r"^(\d+(?:\.\d+)?)(ms|s|m|h)$")
    _MULTIPLIERS = {
        "ms": 0.001,
        "s": 1.0,
        "m": 60.0,
        "h": 3600.0,
    }

    def __init__(self, parent=None, raw=None, **kwargs):
        self.parent = parent
        self.raw = raw
        self.value = 0.0
        self.unit = "s"
        if raw:
            self._parse(raw)

    def _parse(self, raw: str):
        m = self._PATTERN.match(raw)
        if m:
            self.value = float(m.group(1))
            self.unit = m.group(2)

    def to_seconds(self) -> float:
        return self.value * self._MULTIPLIERS[self.unit]

    def __repr__(self):
        return f"Duration({self.value}{self.unit})"


class RateGoal:
    def __init__(
        self,
        parent=None,
        name=None,
        entity=None,
        interval=None,
        tolerance=None,
        jitter=None,
        window=None,
        timeConstraints=None,
        description=None,
        timeout=None,
        tags=None,
        **kwargs,
    ):
        self.parent = parent
        self.name = name
        self.entity = entity
        self.interval = interval
        self.tolerance = tolerance
        self.jitter = jitter
        self.window = window
        self.timeConstraints = timeConstraints or []
        self.description = description
        self.timeout = timeout
        self.tags = tags or []


class LatencyGoal:
    def __init__(
        self,
        parent=None,
        name=None,
        triggerCondition=None,
        triggerEntity=None,
        responseCondition=None,
        responseEntity=None,
        within=None,
        timeConstraints=None,
        description=None,
        timeout=None,
        tags=None,
        **kwargs,
    ):
        self.parent = parent
        self.name = name
        self.triggerCondition = triggerCondition
        self.triggerEntity = triggerEntity
        self.responseCondition = responseCondition
        self.responseEntity = responseEntity
        self.within = within
        self.timeConstraints = timeConstraints or []
        self.description = description
        self.timeout = timeout
        self.tags = tags or []


class OrderingGoal:
    def __init__(
        self,
        parent=None,
        name=None,
        sequence=None,
        within=None,
        timeConstraints=None,
        description=None,
        timeout=None,
        tags=None,
        **kwargs,
    ):
        self.parent = parent
        self.name = name
        self.sequence = sequence or []
        self.within = within
        self.timeConstraints = timeConstraints or []
        self.description = description
        self.timeout = timeout
        self.tags = tags or []


class DeadlineGoal:
    def __init__(
        self,
        parent=None,
        name=None,
        condition=None,
        by=None,
        after=None,
        timeConstraints=None,
        description=None,
        timeout=None,
        tags=None,
        **kwargs,
    ):
        self.parent = parent
        self.name = name
        self.condition = condition
        self.by = by
        self.after = after
        self.timeConstraints = timeConstraints or []
        self.description = description
        self.timeout = timeout
        self.tags = tags or []

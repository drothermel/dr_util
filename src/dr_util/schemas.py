from dataclasses import MISSING, dataclass
from enum import Enum
from typing import Any

from dr_util.schema_utils import lenient_validate


class ConfigType(Enum):
    """Enumeration of available configuration types."""

    USES_METRICS = "uses_metrics"


def get_schema(config_type: str) -> type[Any] | None:
    match config_type:
        case ConfigType.USES_METRICS.value:
            return UsingMetricsConfig
    return None


#########################################################
#             Config Definitions
#########################################################


@lenient_validate
@dataclass
class MetricsInitConfig:
    """Configuration for metrics initialization."""

    batch_size: str = "list"


@lenient_validate
@dataclass
class MetricsConfig:
    """Configuration for metrics collection and logging."""

    loggers: list[str] = MISSING  # type: ignore[assignment]
    init: type = MetricsInitConfig


#########################################################
#             Config Interface Definitions
#########################################################


@lenient_validate
@dataclass
class UsingMetricsConfig:
    """Configuration for systems that use metrics."""

    metrics: type = MetricsConfig

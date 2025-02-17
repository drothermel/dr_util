from typing import List, Type, Optional
from dataclasses import dataclass, fields, asdict, MISSING
from enum import Enum

from dr_util.schema_utils import lenient_validate


class ConfigType(Enum):
    USES_METRICS = "uses_metrics"

def get_schema(config_type):
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
    half_moon: str = MISSING
    fields_bay: str = MISSING
    loss: str = MISSING
    batch_size: str = "list"


@lenient_validate
@dataclass
class MetricsConfig:
    loggers: List = MISSING
    init: Type = MetricsInitConfig


#########################################################
#             Config Interface Definitions 
#########################################################

@lenient_validate
@dataclass
class UsingMetricsConfig:
    resources: List = MISSING
    metrics: Type = MetricsConfig


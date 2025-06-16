import logging
from enum import Enum
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Any, Union, cast

if TYPE_CHECKING:
    from collections.abc import Callable

import jsonlines
from omegaconf import DictConfig, OmegaConf

import dr_util.print_utils as pu

# ---------------------------------------------------------
#                     Logger Classes
# ---------------------------------------------------------


class LoggerType(Enum):
    """Enum for different logger types."""

    HYDRA = "hydra"
    JSON = "json"


def create_logger(
    cfg: DictConfig, logger_type: str
) -> Union["HydraLogger", "JsonLogger"]:
    match logger_type:
        case LoggerType.HYDRA.value:
            return HydraLogger(cfg)
        case LoggerType.JSON.value:
            return JsonLogger(cfg)
    assert False, f">> Unknown logger type: {logger_type}"


class HydraLogger:
    """Logger that outputs to Hydra's logging system."""

    def __init__(self, cfg: DictConfig) -> None:
        """Initialize HydraLogger."""
        # Hydra sets up the logging cfg at start of run
        self.type = LoggerType.HYDRA
        self.cfg = cfg
        self.log(">> Initialize HydraLogger")
        self.pretty_log_dict = False

    @singledispatchmethod
    def log(self, value: Any) -> None:  # noqa: ANN401
        """Log a value using the appropriate logging method."""
        logging.info(str(value))

    @log.register(str)
    def _(self, value: str) -> None:
        logging.info(value)

    @log.register(DictConfig)
    def _(self, value: DictConfig) -> None:
        pu.log_cfg_str(value)

    @log.register(list)
    def _(self, value: list[Any]) -> None:
        if len(value) > 0 and all(isinstance(v, str) for v in value):
            # Assume its a block of text, print directly as such
            # Extra newlines to avoid indent mismatch
            logging.info("\n".join(["", *value, ""]))
        else:
            logging.info(str(value))

    @log.register(dict)
    def _(self, value: dict[str, Any]) -> None:
        if self.pretty_log_dict:
            dict_str = pu.get_dict_str(value, indent=2)
            logging.info(dict_str)
        else:
            logging.info(value)


class JsonLogger:
    """Logger that outputs to JSON lines file."""

    def __init__(self, cfg: DictConfig) -> None:
        """Initialize JsonLogger."""
        self.type = LoggerType.JSON
        self.cfg = cfg

        # Setup json file
        self.path = f"{cfg.paths.run_dir}/json_out.jsonl"
        self.writer = None
        try:
            self.writer = jsonlines.open(self.path, "a")
        except OSError:
            logging.warning(">> Could not open jsonlines log file")

        logging.info(">> Initialize JSON Logger")
        logging.info(f"    - output path: {self.path}")

    @singledispatchmethod
    def log(self, value: Any) -> None:  # noqa: ANN401
        """Log a value using singledispatch based on type."""
        if self.writer is not None:
            self.writer.write({"type": type(value).__name__, "value": value})

    @log.register(dict)
    def _(self, value: dict[str, Any]) -> None:
        if self.writer is not None:
            self.writer.write(value)

    @log.register(DictConfig)
    def _(self, value: DictConfig) -> None:
        if self.writer is not None:
            resolved_val = OmegaConf.to_container(value, resolve=True)
            self.writer.write({"type": "dict_config", "value": resolved_val})


# ---------------------------------------------------------
#                     Metrics Classes
# ---------------------------------------------------------

BATCH_KEY = "batch_size"


class MetricType(Enum):
    """Enumeration of supported metric aggregation types."""

    INT = "int"
    LIST = "list"
    BATCH_WEIGHTED_AVG_LIST = "batch_weighted_avg_list"


def add_sum(data: dict[str, Any], key: str, val: Any) -> None:  # noqa: ANN401
    data[key] += val


def add_list(data: dict[str, Any], key: str, val: Any) -> None:  # noqa: ANN401
    data[key].append(val)


def agg_passthrough(data: dict[str, Any], key: str) -> Any:  # noqa: ANN401
    return data[key]


def agg_none(data: dict[str, Any], key: str) -> None:  # noqa: ARG001
    return None


def agg_batch_weighted_list_avg(data: dict[str, Any], key: str) -> float:
    assert BATCH_KEY in data
    weighted_sum = sum(
        [data[key][i] * data[BATCH_KEY][i] for i in range(len(data[key]))]
    )
    total_samples = sum(data[BATCH_KEY])
    return float(weighted_sum * 1.0 / total_samples)


class MetricsSubgroup:
    """Handles metrics collection for a specific group (e.g., train, val)."""

    def __init__(
        self,
        cfg: DictConfig,
        name: str = "",
        metrics: Any | None = None,  # noqa: ANN401
    ) -> None:
        """Initialize MetricsSubgroup.

        Args:
            cfg: Configuration object containing metrics settings.
            name: Name of the metrics group.
            metrics: Optional metrics configuration.
        """
        self.name = name
        self.metrics = metrics
        self.data_structure = cfg.metrics.init
        self.data: dict[str, Any] = {}
        self.add_fxns: dict[str, Callable[[dict[str, Any], str, Any], None]] = {}
        self.agg_fxns: dict[str, Callable[[dict[str, Any], str], Any]] = {}

        self._init_data()

    def _init_data(self) -> None:
        if self.data_structure is None:
            return

        for key, data_type in self.data_structure.items():
            match data_type:
                case MetricType.INT.value:
                    self.data[key] = 0
                    self.add_fxns[key] = add_sum
                    self.agg_fxns[key] = agg_passthrough
                case MetricType.LIST.value:
                    self.data[key] = []
                    self.add_fxns[key] = add_list
                    self.agg_fxns[key] = agg_none
                case MetricType.BATCH_WEIGHTED_AVG_LIST.value:
                    self.data[key] = []
                    self.add_fxns[key] = add_list
                    self.agg_fxns[key] = agg_batch_weighted_list_avg

    def _add_tuple(self, key: str, val: Any) -> None:  # noqa: ANN401
        assert key in self.data, f">> Invalid Key: {key}"
        if val is None:
            return
        self.add_fxns[key](self.data, key, val)

    @singledispatchmethod
    def add(self, data: Any, ns: int = 1) -> None:  # noqa: ARG002, ANN401
        """Add data to metrics collection - base method for single dispatch."""
        assert False, f">> Unexpected data type: {type(data)}"

    @add.register(tuple)
    def _(self, data: tuple[str, Any], ns: int = 1) -> None:
        assert len(data) == len(("key", "val"))
        self._add_tuple(*data)
        self._add_tuple(BATCH_KEY, ns)

    @add.register(dict)
    def _(self, data: dict[str, Any], ns: int = 1) -> None:
        for key, val in data.items():
            self._add_tuple(key, val)
        self._add_tuple(BATCH_KEY, ns)

    def agg(self) -> dict[str, Any]:
        """Aggregate collected metrics data.

        Returns:
            Dictionary of aggregated metrics.
        """
        agg_data = {}
        for key in self.data:
            agg_val = self.agg_fxns[key](self.data, key)
            if agg_val is not None:
                agg_data[key] = agg_val
        return agg_data


class Metrics:
    """Main metrics collection and logging system."""

    def __init__(self, cfg: DictConfig) -> None:
        """Initialize Metrics system.

        Args:
            cfg: Configuration object containing metrics and logging settings.
        """
        self.cfg = cfg
        self.group_names = ["train", "val"]

        # Initialize subgroups and loggers
        self.groups = {name: MetricsSubgroup(cfg, name) for name in self.group_names}
        self.loggers = [create_logger(cfg, lt) for lt in cfg.metrics.loggers]

    def log(self, value: Any) -> None:  # noqa: ANN401  # noqa: ANN401
        """Log a value to all configured loggers.

        Args:
            value: The value to log.
        """
        for logger in self.loggers:
            logger.log(value)

    def train(self, data: tuple[str, Any] | dict[str, Any], ns: int = 1) -> None:
        """Add training data to metrics.

        Args:
            data: Training data as tuple (key, value) or dict.
            ns: Number of samples (batch size).
        """
        self.groups["train"].add(data, ns=ns)

    def val(self, data: tuple[str, Any] | dict[str, Any], ns: int = 1) -> None:
        """Add validation data to metrics.

        Args:
            data: Validation data as tuple (key, value) or dict.
            ns: Number of samples (batch size).
        """
        self.groups["val"].add(data, ns=ns)

    def agg(self, data_name: str) -> dict[str, Any]:
        """Aggregate metrics for a specific data group.

        Args:
            data_name: Name of the data group (e.g., 'train', 'val').

        Returns:
            Dictionary of aggregated metrics.
        """
        assert data_name in self.groups, f">> Invalid Data Name: {data_name}"
        return self.groups[data_name].agg()

    def agg_log(self, data_name: str) -> None:
        """Aggregate metrics and log the results.

        Args:
            data_name: Name of the data group to aggregate and log.
        """
        log_dict = {
            "title": f"agg_{data_name}",
            "data_name": data_name,
            "agg_stats": {},
        }
        agg_data = self.agg(data_name)
        for key in self.cfg.metrics.init:
            if key in agg_data:
                cast(dict[str, Any], log_dict["agg_stats"])[key] = agg_data[key]

        self.log(log_dict)

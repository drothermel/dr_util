import logging
import pprint
from enum import Enum
from functools import singledispatch, singledispatchmethod

from omegaconf import DictConfig, OmegaConf

# ---------------------------------------------------------
#                         Log Cfg
# ---------------------------------------------------------


@singledispatch
def cfg_to_loggable_lines(cfg):
    logging.warn(f">> Unexpected cfg type: {type(cfg)}")
    return [str(cfg)]  # default, just stringify


@cfg_to_loggable_lines.register(dict)
def _(cfg):
    cfg_str = str(cfg)
    return cfg_str.strip("\n").split("\n")


@cfg_to_loggable_lines.register(DictConfig)
def _(cfg):
    resolved_cfg = OmegaConf.to_container(cfg, resolve=True)
    cfg_str = OmegaConf.to_yaml(resolved_cfg)
    return cfg_str.strip("\n").split("\n")


def get_cfg_str(cfg):
    return "\n".join(
        [
            "\n",
            "=" * 19 + "   Config   " + "=" * 19,
            *cfg_to_loggable_lines(cfg),
            "=" * 50,
            "",
        ]
    )


# ---------------------------------------------------------
#                     Logger Classes
# ---------------------------------------------------------


class LoggerType(Enum):
    HYDRA = "hydra"
    JSON = "json"

def create_logger(cfg, logger_type):
    match logger_type:
        case LoggerType.HYDRA.value:
            return HydraLogger(cfg)
        case LoggerType.JSON.value:
            assert False, "Not implemented yet"
    assert False, f">> Unknown logger type: {logger_type}"

class HydraLogger:
    def __init__(self, cfg):
        # Hydra sets up the logging cfg at start of run
        self.type = LoggerType.HYRDA
        self.cfg = cfg
        self.log(">> Initialize HydraLogger")

    @singledispatchmethod
    def log(self, value):
        logging.info(pprint.pformat(value))

    @log.register(str)
    def _(self, value):
        logging.info(value)

    @log.register(DictConfig)
    def _(self, value):
        logging.info(get_cfg_str(value))

    @log.register(list)
    def _(self, value):
        if len(value) > 0 and all(isinstance(v, str) for v in value):
            # Assume its a block of text, print directly as such
            # Extra newlines to avoid indent mismatch
            logging.info("\n".join(["", *value, ""]))
        else:
            logging.info(pprint.pformat(value))

    @log.register(dict)
    def _(self, value):
        dict_str = pprint.pformat(value)
        # Extra newlines to avoid indent mismatch
        logging.info("\n" + dict_str + "\n")


# ---------------------------------------------------------
#                     Metrics Classes
# ---------------------------------------------------------

BATCH_KEY = "batch_size"


class MetricType(Enum):
    INT = "int"
    LIST = "list"
    BATCH_WEIGHTED_AVG_LIST = "batch_weighted_avg_list"


def add_sum(data, key, val):
    data[key] += val


def add_list(data, key, val):
    data[key].append(val)


def agg_passthrough(data, key):
    return data[key]


def agg_none(data, key):  # noqa: ARG001
    return None


def agg_batch_weighted_list_avg(data, key):
    assert BATCH_KEY in data
    weighted_sum = sum(
        [data[key][i] * data[BATCH_KEY][i] for i in range(len(data[key]))]
    )
    total_samples = sum(data[BATCH_KEY])
    return weighted_sum * 1.0 / total_samples


class MetricsSubgroup:
    def __init__(self, cfg, name="", metrics=None):
        self.name = name
        self.metrics = metrics
        self.data_structure = cfg.metrics.init
        self.data = {}
        self.add_fxns = {}
        self.agg_fxns = {}

        self._init_data()

    def _init_data(self):
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

    def _add_tuple(self, key, val):
        assert key in self.data, f">> Invalid Key: {key}"
        if val is None:
            return
        self.add_fxns[key](self.data, key, val)

    @singledispatchmethod
    def add(self, data, ns=1):  # noqa: ARG002 (unused args)
        assert False, f">> Unexpected data type: {type(data)}"  # noqa

    @add.register(tuple)
    def _(self, data, ns=1):
        assert len(data) == len(("key", "val"))
        self._add_tuple(*data)
        self._add_tuple(BATCH_KEY, ns)

    @add.register(dict)
    def _(self, data, ns=1):
        for key, val in data.items():
            self._add_tuple(key, val)
        self._add_tuple(BATCH_KEY, ns)

    def agg(self):
        agg_data = {}
        for key in self.data:
            agg_val = self.agg_fxns[key](self.data, key)
            if agg_val is not None:
                agg_data[key] = agg_val
        return agg_data


class Metrics:
    def __init__(self, cfg):
        self.cfg = cfg
        self.group_names = ["train", "val"]

        # Initialize subgroups and loggers
        self.groups = {name: MetricsSubgroup(cfg, name) for name in self.group_names}
        self.loggers = [create_logger(cfg, lt) for lt in cfg.metrics.loggers]

    def log(self, value):
        for logger in self.loggers:
            logger.log(value)

    def train(self, data, ns=1):
        self.groups["train"].add(data, ns=ns)

    def val(self, data, ns=1):
        self.groups["val"].add(data, ns=ns)

    def agg(self, data_name):
        assert data_name in self.groups, f">> Invalid Data Name: {data_name}"
        return self.groups[data_name].agg()

    def agg_log(self, data_name):
        self.log(f":: Aggregate {data_name} ::")
        agg_data = self.agg(data_name)
        for key in self.cfg.metrics.init:
            if key in agg_data:
                val = agg_data[key]
                if isinstance(val, float) and (val < 1 or val > -1):
                    self.log(f"  - {key:20} | {val:0.4f}")
                elif isinstance(val, float):
                    self.log(f"  - {key:20} | {val:0.2f}")
                else:
                    self.log(f"  - {key:20} | {val}")

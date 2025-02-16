import io
from contextlib import redirect_stdout
from types import SimpleNamespace

import pytest

from dr_util.metrics import (
    BATCH_KEY,
    Metrics,
    MetricsGroup,
)

# ---------------------------
# Tests for MetricsGroup
# ---------------------------


@pytest.fixture
def dummy_cfg():
    """
    Create a dummy configuration with three metrics:
      - "loss" as an integer metric (using sum aggregation)
      - "preds" as a list metric (which uses agg_none and is not returned in agg)
      - "weighted" as a weighted average metric (which requires BATCH_KEY)
    Include BATCH_KEY in the config as a list so that its values can be accumulated.
    """
    return SimpleNamespace(
        metrics={  # Uses MetricType Enum
            "loss": "int",  # INT.value
            "preds": "list",  # LIST.value
            "weighted": "batch_weighted_avg_list",  # BATCH_WEIGHTED_AVG_LIST.value
            BATCH_KEY: "list",  # This must be a list so that add_list is used.
        }
    )


def test_metrics_group_initialization(dummy_cfg):
    mg = MetricsGroup(dummy_cfg, name="test")
    # Check that the metrics are initialized correctly.
    assert mg.data["loss"] == 0
    assert mg.data["preds"] == []
    assert mg.data["weighted"] == []
    assert mg.data[BATCH_KEY] == []


def test_metrics_group_add_tuple(dummy_cfg):
    mg = MetricsGroup(dummy_cfg, name="test")
    test_loss_val = 5

    # Add a tuple for an integer metric ("loss").
    mg.add(("loss", test_loss_val))
    # The add method should:
    #   - update "loss" via add_sum (0 + 5)
    #   - append the default ns (1) to the batch list.
    assert mg.data["loss"] == test_loss_val
    assert mg.data[BATCH_KEY] == [1]

    # Add a tuple for a list metric ("preds").
    mg.add(("preds", "a"))
    assert mg.data["preds"] == ["a"]
    # Every add call appends ns to the batch, even if the data value is None.
    assert mg.data[BATCH_KEY] == [1, 1]

    # Add a tuple where the value is None.
    mg.add(("loss", None))
    # The None value should not change the metric value but still add a batch entry.
    assert mg.data["loss"] == test_loss_val
    assert mg.data[BATCH_KEY] == [1, 1, 1]


def test_metrics_group_add_dict(dummy_cfg):
    mg = MetricsGroup(dummy_cfg, name="test")
    test_metric_dict = {"loss": 2, "preds": "b", "weighted": 30}
    test_ns = 2

    # Use a dict input to add values for several metrics at once.
    mg.add(test_metric_dict, ns=test_ns)
    # For "loss": initial 0 + 2 = 2; for "preds": [] becomes ["b"];
    # for "weighted": [] becomes [30]; and a batch value of 2 is appended.
    assert mg.data["loss"] == test_metric_dict["loss"]
    assert mg.data["preds"] == [test_metric_dict["preds"]]
    assert mg.data["weighted"] == [test_metric_dict["weighted"]]
    assert mg.data[BATCH_KEY] == [test_ns]


def test_metrics_group_aggregation(dummy_cfg):
    mg = MetricsGroup(dummy_cfg, name="test")

    # Perform two add calls to build up data.
    # First call: add ("weighted", 10) with ns=2.
    mg.add(("weighted", 10), ns=2)
    # Second call: add ("weighted", 20) with ns=3.
    mg.add(("weighted", 20), ns=3)
    # After these calls:
    #   mg.data["weighted"] should be [10, 20]
    #   mg.data[BATCH_KEY] should be [2, 3]
    assert mg.data["weighted"] == [10, 20]
    assert mg.data[BATCH_KEY] == [2, 3]

    # The aggregator for "weighted" computes a weighted average:
    #   weighted_sum = 10*2 + 20*3 = 20 + 60 = 80
    #   total_samples = 2 + 3 = 5
    #   average = 80 / 5 = 16.0
    agg_result = mg.agg()
    assert agg_result["weighted"] == pytest.approx(16.0)

    # For an integer metric using agg_passthrough, we test similarly.
    test_loss = 7
    mg.add(("loss", test_loss))
    agg_result = mg.agg()
    assert agg_result["loss"] == test_loss
    # Note: "preds" and the batch key use agg_none so they are omitted.


def test_metrics_group_invalid_inputs(dummy_cfg):
    mg = MetricsGroup(dummy_cfg, name="test")

    # Passing a key that is not in the config should raise an assertion.
    with pytest.raises(AssertionError, match="Invalid Key"):
        mg.add(("nonexistent", 10))

    # Passing an unsupported type (e.g. int) should trigger the default singledispatch.
    with pytest.raises(AssertionError, match="Unexpected data type"):
        mg.add(123)

    # Passing a tuple of wrong length (should be exactly 2) raises an assertion.
    with pytest.raises(AssertionError):
        mg.add(("loss",))  # tuple length != 2


def test_metrics_group_no_config():
    # When cfg.metrics is None, the MetricsGroup init is an empty data dict.
    cfg = SimpleNamespace(metrics=None)
    mg = MetricsGroup(cfg, "empty")
    assert mg.data == {}


# ---------------------------
# Tests for Metrics (the top-level class)
# ---------------------------


@pytest.fixture
def dummy_metrics():
    cfg = SimpleNamespace(
        metrics={
            "loss": "int",
            "preds": "list",
            "weighted": "batch_weighted_avg_list",
            BATCH_KEY: "list",
        }
    )
    return Metrics(cfg)


def test_metrics_train_and_val(dummy_metrics):
    # Test the two groups ("train" and "val") separately.
    metrics_obj = dummy_metrics
    test_loss = 10

    # For the "train" group, add a tuple.
    metrics_obj.train(("loss", test_loss))
    # For the "train" group, the "loss" metric should now be 10.
    train_agg = metrics_obj.agg("train")
    assert train_agg["loss"] == test_loss

    # For the "val" group, add a dict input.
    metrics_obj.val({"weighted": 40}, ns=2)
    # For the "val" group, "weighted" should now be [40] with a batch value [2].
    # Its aggregation computes 40*2 / 2 = 40.0.
    val_agg = metrics_obj.agg("val")
    assert val_agg["weighted"] == pytest.approx(40.0)


def test_metrics_invalid_group(dummy_metrics):
    metrics_obj = dummy_metrics

    with pytest.raises(AssertionError, match="Invalid Data Name"):
        metrics_obj.agg("invalid_group")


def test_metrics_agg_print(dummy_metrics):
    metrics_obj = dummy_metrics
    # Add a value so that aggregation produces some output.
    metrics_obj.train(("loss", 5))
    f = io.StringIO()
    with redirect_stdout(f):
        metrics_obj.agg_print("train")
    output = f.getvalue()
    # Check that the printed output contains the header and the "loss" metric.
    assert ":: Aggregate train ::" in output
    assert "loss" in output
    # Since loss is an int, it will be printed without extra formatting.

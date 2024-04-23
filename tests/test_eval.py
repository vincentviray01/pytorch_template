import os

import pytest
from hydra.core.hydra_config import HydraConfig
from omegaconf import open_dict

from src.eval import evaluate
from src.train import train


@pytest.mark.slow
def test_train_eval_predict(tmp_path, cfg_train, cfg_eval):
    """Train for 1 epoch with `train.py`, evaluate and predict with
    `eval.py`"""
    assert str(tmp_path) == cfg_train.paths.output_dir
    assert str(tmp_path) == cfg_eval.paths.output_dir

    # train for 1 epoch
    with open_dict(cfg_train):
        cfg_train.trainer.max_epochs = 1
        cfg_train.test = True

    HydraConfig().set_config(cfg_train)
    train_metric_dict, _ = train(cfg_train)

    assert "last.ckpt" in os.listdir(tmp_path / "checkpoints")

    # evaluate
    with open_dict(cfg_eval):
        cfg_eval.ckpt_path = str(tmp_path / "checkpoints" / "last.ckpt")

    HydraConfig().set_config(cfg_eval)
    test_metric_dict, _ = evaluate(cfg_eval)

    metric = "MulticlassAccuracy"
    assert test_metric_dict[f"{metric}/test"] > 0.0
    assert (
        abs(
            train_metric_dict[f"{metric}/test"].item()
            - test_metric_dict[f"{metric}/test"].item()
        )
        < 0.001
    )

    # predict
    with open_dict(cfg_eval):
        cfg_eval.predict = True

    HydraConfig().set_config(cfg_eval)
    evaluate(cfg_eval)

    assert "predictions.json" in os.listdir(tmp_path / "predictions")

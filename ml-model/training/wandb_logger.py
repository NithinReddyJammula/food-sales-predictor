"""
wandb_logger.py
────────────────
WandB → New Relic bridge.

Intercepts WandB run events (metrics, hyperparams, alerts, finish) and forwards
them as structured OpenTelemetry log records so they appear in New Relic Logs
under service.name='food-sales-predictor.training'.

────────────────────────────────────────────────────────────────
Usage with raw WandB API (standalone training script):
────────────────────────────────────────────────────────────────

    from ml_model.training.wandb_logger import NewRelicWandbBridge
    import wandb

    run = wandb.init(project="food-sales-predictor", config={...})
    bridge = NewRelicWandbBridge(run)

    for epoch in range(epochs):
        metrics = {"train_loss": ..., "val_loss": ...}
        wandb.log(metrics)
        bridge.log_metrics(metrics, step=epoch)   # mirrors to New Relic

    bridge.finish(status="success")
    wandb.finish()

────────────────────────────────────────────────────────────────
Usage with PyTorch Lightning WandbLogger:
────────────────────────────────────────────────────────────────

    from ml_model.training.wandb_logger import PLNewRelicCallback

    trainer = pl.Trainer(
        logger=wandb_logger,
        callbacks=[PLNewRelicCallback()],
        ...
    )
"""

import logging
import os
from typing import Any, Dict, Optional

# Ensure Observability is active before logging
def _init_observability():
    try:
        import sys
        from pathlib import Path
        data_pipeline_dir = str(Path(__file__).resolve().parent.parent.parent / "data-pipeline")
        if data_pipeline_dir not in sys.path:
            sys.path.insert(0, data_pipeline_dir)
        from config.util.monitoring import Observability
        Observability.initialize()
    except Exception:
        pass

_init_observability()

_logger = logging.getLogger("food-sales-predictor.training.wandb")


# ── Standalone WandB bridge ───────────────────────────────────────────────────

class NewRelicWandbBridge:
    """
    Wraps a `wandb.Run` and mirrors every logged event to New Relic.
    """

    def __init__(self, run: Any):
        self._run = run
        _logger.info("WandB run started", extra={
            "wandb.run_id": getattr(run, "id", "unknown"),
            "wandb.run_name": getattr(run, "name", "unknown"),
            "wandb.project": getattr(run, "project", "unknown"),
            "wandb.entity": getattr(run, "entity", "unknown"),
            "wandb.url": getattr(run, "url", ""),
        })

    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Call after every wandb.log() to mirror metrics to New Relic."""
        extra = {
            "wandb.event": "metrics",
            "wandb.run_id": getattr(self._run, "id", "unknown"),
            "wandb.step": step,
        }
        extra.update({f"wandb.metric.{k}": v for k, v in metrics.items()})
        _logger.info(
            f"WandB metrics: step={step} | " + " | ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in metrics.items()),
            extra=extra,
        )

    def log_hyperparams(self, params: Dict[str, Any]):
        """Call once to mirror hyperparameters to New Relic."""
        extra = {
            "wandb.event": "hyperparams",
            "wandb.run_id": getattr(self._run, "id", "unknown"),
        }
        extra.update({f"wandb.param.{k}": v for k, v in params.items()})
        _logger.info("WandB hyperparameters logged", extra=extra)

    def log_alert(self, title: str, text: str, level: str = "INFO"):
        """Mirror a wandb.alert() to New Relic."""
        log_fn = _logger.warning if level.upper() in ("WARN", "WARNING") else _logger.error if level.upper() == "ERROR" else _logger.info
        log_fn(f"WandB alert: {title} — {text}", extra={
            "wandb.event": "alert",
            "wandb.run_id": getattr(self._run, "id", "unknown"),
            "wandb.alert.title": title,
            "wandb.alert.level": level,
        })

    def finish(self, status: str = "success"):
        """Call when the training run ends to emit a completion log."""
        level = logging.INFO if status == "success" else logging.ERROR
        _logger.log(level, f"WandB run finished: {status}", extra={
            "wandb.event": "run_finish",
            "wandb.run_id": getattr(self._run, "id", "unknown"),
            "wandb.run_name": getattr(self._run, "name", "unknown"),
            "wandb.status": status,
            "wandb.summary": dict(getattr(self._run, "summary", {}) or {}),
        })


# ── PyTorch Lightning Callback ────────────────────────────────────────────────

class PLNewRelicCallback:
    """
    PyTorch Lightning Callback that mirrors WandB events to New Relic.

    Add to trainer callbacks:
        trainer = pl.Trainer(callbacks=[PLNewRelicCallback()])
    """

    def on_train_start(self, trainer, pl_module):
        try:
            import wandb
            if wandb.run:
                self._bridge = NewRelicWandbBridge(wandb.run)
                self._bridge.log_hyperparams(dict(trainer.logger.experiment.config or {}))
        except Exception:
            self._bridge = None

    def on_train_epoch_end(self, trainer, pl_module):
        if not getattr(self, "_bridge", None):
            return
        metrics = {k: float(v) for k, v in trainer.logged_metrics.items() if v is not None}
        if metrics:
            self._bridge.log_metrics(metrics, step=trainer.current_epoch)

    def on_validation_epoch_end(self, trainer, pl_module):
        if not getattr(self, "_bridge", None):
            return
        metrics = {k: float(v) for k, v in trainer.logged_metrics.items()
                   if v is not None and "val" in k}
        if metrics:
            self._bridge.log_metrics(metrics, step=trainer.current_epoch)

    def on_exception(self, trainer, pl_module, exception):
        if getattr(self, "_bridge", None):
            self._bridge.finish(status="failed")
            _logger.error(f"Training failed with exception: {exception}", extra={
                "wandb.event": "exception",
                "error": str(exception),
            })

    def on_train_end(self, trainer, pl_module):
        if getattr(self, "_bridge", None):
            self._bridge.finish(status="success")

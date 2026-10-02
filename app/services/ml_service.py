"""
app/services/ml_service.py
==========================
Trevolk Forecasting Engine — ML Service (Singleton)

Responsibilities:
  - Lazily load the XGBoost model from disk exactly once (thread-safe singleton).
  - Build a 7-day feature matrix from the incoming ForecastRequest.
  - Run a batch prediction and assemble the structured ForecastResponse.

Design decisions:
  - Thread-safe singleton via a class-level lock (_lock) and double-checked
    locking so the model is never loaded more than once even under concurrent
    startup traffic.
  - StoreType, Assortment, and StateHoliday are mocked with safe integer
    defaults (0) because the frontend does not collect these fields; when
    the real encoding is available, replace the constants below.
  - Predictions are clipped to >= 0 (sales cannot be negative).
  - optimal_price_adjustment is derived from the coefficient of variation
    of the 7-day predictions scaled to a ±10 % band — a lightweight signal
    without a second model.
"""

from __future__ import annotations

import logging
import threading
from datetime import timedelta
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd

from app.schemas.predict import DailyForecast, ForecastRequest, ForecastResponse

logger = logging.getLogger("trevolk.ml_service")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_PATH = Path(__file__).resolve().parents[2] / "trevolk_sales_model.pkl"

# Exact feature order the XGBoost model was trained on — DO NOT reorder.
FEATURE_ORDER: List[str] = [
    "Store",
    "DayOfWeek",
    "Promo",
    "SchoolHoliday",
    "StoreType",
    "Assortment",
    "CompetitionDistance",
    "Year",
    "Month",
    "Day",
    "WeekOfYear",
    "StateHoliday",
]

# Mock defaults for fields not supplied by the frontend.
# Replace with real label-encoded values once available.
DEFAULT_STORE_TYPE: int = 0      # encoded 'a' → 0
DEFAULT_ASSORTMENT: int = 0      # encoded 'a' → 0
DEFAULT_STATE_HOLIDAY: int = 0   # '0' (no holiday) → 0

FORECAST_HORIZON_DAYS: int = 7
CONFIDENCE_SCORE: float = 95.0   # static model confidence (replace with RMSE-derived CI)

# Short weekday names indexed by pandas dayofweek (0 = Monday)
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------------------------------------------------------------------------
# Singleton ML Service
# ---------------------------------------------------------------------------
class MLService:
    """
    Thread-safe singleton that owns the loaded XGBoost model and exposes
    a single public method: ``predict(request)`` → ``ForecastResponse``.

    Usage:
        service = MLService.get_instance()
        response = service.predict(forecast_request)
    """

    _instance: Optional["MLService"] = None
    _lock: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # Singleton constructor
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._model = None
        self._model_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "MLService":
        """Return the shared singleton, creating it on first call."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:          # double-checked locking
                    cls._instance = cls()
                    logger.debug("MLService singleton created.")
        return cls._instance

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------
    def load_model(self) -> None:
        """
        Load the model from disk into memory.
        Idempotent — calling multiple times is safe and cheap (no-op after
        the first successful load).
        """
        if self._model is not None:
            return

        with self._model_lock:
            if self._model is not None:            # double-checked inside lock
                return

            logger.info("Loading model from: %s", MODEL_PATH)

            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Model file not found at '{MODEL_PATH}'. "
                    "Ensure trevolk_sales_model.pkl is placed in the project root."
                )

            self._model = joblib.load(MODEL_PATH)
            logger.info("Model loaded successfully. Type: %s", type(self._model).__name__)

    def is_ready(self) -> bool:
        """Return True if the model is loaded and ready for inference."""
        return self._model is not None

    # ------------------------------------------------------------------
    # Feature Engineering (private)
    # ------------------------------------------------------------------
    def _build_feature_matrix(self, request: ForecastRequest) -> pd.DataFrame:
        """
        Expand a single ForecastRequest into a (7 × 12) feature DataFrame —
        one row per forecast day, columns in FEATURE_ORDER.

        Steps:
          1. Generate 7 consecutive dates starting from forecast_start_date.
          2. Decompose each date into Year, Month, Day, DayOfWeek, WeekOfYear.
          3. Broadcast scalar fields (Store, Promo, …) across all 7 rows.
          4. Fill mocked categorical fields with integer defaults.
          5. Reindex columns to enforce strict FEATURE_ORDER.
        """
        start = pd.Timestamp(request.forecast_start_date)
        dates = [start + timedelta(days=i) for i in range(FORECAST_HORIZON_DAYS)]

        rows = []
        for ts in dates:
            rows.append(
                {
                    # --- from request ---
                    "Store": request.store_id,
                    "Promo": int(request.promotion_active),
                    "SchoolHoliday": int(request.school_holiday),
                    "CompetitionDistance": request.competition_distance,
                    # --- derived from date ---
                    "DayOfWeek": ts.dayofweek + 1,          # Rossmann: 1=Mon … 7=Sun
                    "Year": ts.year,
                    "Month": ts.month,
                    "Day": ts.day,
                    "WeekOfYear": int(ts.isocalendar().week),
                    # --- mocked categoricals ---
                    "StoreType": DEFAULT_STORE_TYPE,
                    "Assortment": DEFAULT_ASSORTMENT,
                    "StateHoliday": DEFAULT_STATE_HOLIDAY,
                }
            )

        df = pd.DataFrame(rows, columns=FEATURE_ORDER)
        logger.debug("Feature matrix shape: %s", df.shape)
        return df, dates

    # ------------------------------------------------------------------
    # KPI Derivations (private)
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_price_adjustment(predictions: np.ndarray) -> float:
        """
        Lightweight price-adjustment signal.

        Logic: coefficient of variation (CV) of the 7-day predictions,
        scaled to a ±10 % band.  High demand volatility → positive adjustment
        (charge more on spike days); flat demand → near-zero adjustment.

        Returns a float rounded to 1 decimal place, clamped to [-10, +10].
        """
        mean = predictions.mean()
        if mean == 0:
            return 0.0
        cv = predictions.std() / mean          # normalised volatility [0, 1]
        adjustment = round(float(np.clip(cv * 10, -10.0, 10.0)), 1)
        return adjustment

    # ------------------------------------------------------------------
    # Public Inference API
    # ------------------------------------------------------------------
    def predict(self, request: ForecastRequest) -> ForecastResponse:
        """
        Run a 7-day batch forecast and return a fully structured ForecastResponse.

        Raises:
            RuntimeError: if the model has not been loaded yet.
            ValueError: if the feature matrix cannot be built from the request.
            Exception: propagates any unexpected XGBoost inference errors.
        """
        if not self.is_ready():
            raise RuntimeError(
                "MLService: model is not loaded. Call load_model() first."
            )

        # 1. Build feature matrix
        features_df, dates = self._build_feature_matrix(request)

        # 2. Batch inference
        raw_preds: np.ndarray = self._model.predict(features_df)
        predictions = np.maximum(raw_preds, 0.0)      # clip negatives

        logger.info(
            "Batch prediction | Store=%s  Start=%s  Preds=%s",
            request.store_id,
            request.forecast_start_date,
            predictions.round(2).tolist(),
        )

        # 3. Assemble daily_forecast list
        daily_forecast = [
            DailyForecast(
                date=ts.strftime("%Y-%m-%d"),
                day=DAY_NAMES[ts.dayofweek],
                predicted_sales=round(float(predictions[i]), 2),
            )
            for i, ts in enumerate(dates)
        ]

        # 4. Compute KPIs
        expected_revenue = round(float(predictions.sum()), 2)
        optimal_price_adjustment = self._compute_price_adjustment(predictions)

        return ForecastResponse(
            expected_revenue=expected_revenue,
            optimal_price_adjustment=optimal_price_adjustment,
            confidence_score=CONFIDENCE_SCORE,
            daily_forecast=daily_forecast,
        )

"""
app/api/endpoints.py
====================
Trevolk Forecasting Engine — API Router

Defines all HTTP routes. Business logic is fully delegated to MLService
so this file stays thin and focused on HTTP concerns only:
  - Request validation (via Pydantic, handled automatically by FastAPI).
  - Calling the service layer.
  - Mapping service exceptions to appropriate HTTP error codes.
  - Returning the response.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.predict import ForecastRequest, ForecastResponse
from app.services.ml_service import MLService

logger = logging.getLogger("trevolk.endpoints")

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/predict
# ---------------------------------------------------------------------------
@router.post(
    "/predict",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="7-Day Sales Forecast",
    description=(
        "Accepts store context and a start date, runs the XGBoost model for "
        "7 consecutive days, and returns KPI metrics plus a daily breakdown table."
    ),
    responses={
        200: {"description": "Forecast generated successfully."},
        422: {"description": "Request validation failed — check payload schema."},
        503: {"description": "ML model is not loaded — service is starting up."},
        500: {"description": "Unexpected inference error."},
    },
)
def predict_sales(payload: ForecastRequest) -> ForecastResponse:
    """
    **POST /api/predict**

    **Request** (sent by Next.js frontend):
    ```json
    {
      "store_id": 1,
      "forecast_start_date": "2026-10-02",
      "promotion_active": true,
      "school_holiday": false,
      "competition_distance": 1270.0
    }
    ```

    **Response** (drives KPI cards + forecast table):
    ```json
    {
      "expected_revenue": 57893.5,
      "optimal_price_adjustment": 4.8,
      "confidence_score": 95.0,
      "daily_forecast": [
        {"date": "2026-10-02", "day": "Fri", "predicted_sales": 8257.0},
        ...
      ]
    }
    ```
    """
    service = MLService.get_instance()

    # ------------------------------------------------------------------
    # Guard: model must be ready before serving predictions
    # ------------------------------------------------------------------
    if not service.is_ready():
        logger.error("Prediction requested but model is not loaded.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The forecasting model is not yet loaded. "
                "The service may still be starting up — please retry in a few seconds."
            ),
        )

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    try:
        response = service.predict(payload)
        logger.info(
            "Forecast served | Store=%s  Start=%s  Revenue=%.2f",
            payload.store_id,
            payload.forecast_start_date,
            response.expected_revenue,
        )
        return response

    except FileNotFoundError as exc:
        logger.critical("Model file missing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ValueError as exc:
        logger.warning("Feature engineering error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Feature engineering failed: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected inference error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {exc}",
        )

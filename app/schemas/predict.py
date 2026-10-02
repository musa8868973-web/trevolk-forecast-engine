"""
app/schemas/predict.py
======================
Trevolk Forecasting Engine — Pydantic Request & Response Models

All incoming data is validated here before it reaches business logic.
All outgoing data is serialised from these models for a consistent API contract.
"""

from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------
class ForecastRequest(BaseModel):
    """
    Payload sent by the Next.js frontend for a 7-day rolling sales forecast.

    Field names mirror the frontend form controls exactly so the frontend
    can POST the form state without any key remapping.
    """

    store_id: int = Field(
        ...,
        ge=1,
        description="Rossmann store identifier (positive integer).",
        examples=[1],
    )
    forecast_start_date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="First day of the 7-day forecast window (YYYY-MM-DD).",
        examples=["2026-10-02"],
    )
    promotion_active: bool = Field(
        ...,
        description="True if a promotional campaign is running during the window.",
        examples=[True],
    )
    school_holiday: bool = Field(
        ...,
        description="True if schools are closed during the window.",
        examples=[False],
    )
    competition_distance: float = Field(
        ...,
        ge=0.0,
        description="Distance in metres to the nearest competitor store.",
        examples=[1270.0],
    )

    @field_validator("forecast_start_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Reject strings that are syntactically valid but not real dates (e.g. 2026-02-30)."""
        try:
            date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError(f"'{v}' is not a valid calendar date: {exc}") from exc
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "store_id": 1,
                "forecast_start_date": "2026-10-02",
                "promotion_active": True,
                "school_holiday": False,
                "competition_distance": 1270.0,
            }
        }
    }


# ---------------------------------------------------------------------------
# Response — nested models
# ---------------------------------------------------------------------------
class DailyForecast(BaseModel):
    """One row in the frontend forecast table."""

    date: str = Field(..., description="Calendar date (YYYY-MM-DD).", examples=["2026-10-02"])
    day: str = Field(..., description="Short weekday name.", examples=["Fri"])
    predicted_sales: float = Field(
        ..., description="Model-predicted sales for this day.", examples=[8257.0]
    )


class ForecastResponse(BaseModel):
    """
    Top-level response object.

    Designed to power the KPI cards and the daily breakdown table
    in the Next.js dashboard without any client-side transformation.
    """

    expected_revenue: float = Field(
        ...,
        description="Sum of predicted sales across all 7 forecast days.",
        examples=[57893.5],
    )
    optimal_price_adjustment: float = Field(
        ...,
        description=(
            "Percentage price adjustment recommendation derived from "
            "average demand spikes across the forecast window."
        ),
        examples=[4.8],
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Model confidence percentage for this forecast.",
        examples=[95.0],
    )
    daily_forecast: List[DailyForecast] = Field(
        ...,
        description="Day-by-day breakdown driving the frontend table.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "expected_revenue": 57893.5,
                "optimal_price_adjustment": 4.8,
                "confidence_score": 95.0,
                "daily_forecast": [
                    {"date": "2026-10-02", "day": "Fri", "predicted_sales": 8257.0},
                    {"date": "2026-10-03", "day": "Sat", "predicted_sales": 9412.0},
                ],
            }
        }
    }

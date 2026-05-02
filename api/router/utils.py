import csv
import io
from datetime import datetime

from fastapi.responses import StreamingResponse

from internal.schemas.analytic_models import AnalyticsRead
from internal.schemas.device_models import DeviceRead
from internal.schemas.prediction_models import PredictionRead
from internal.schemas.telemetry_models import TelemetryRead


def _validate_model_list(
        model_list: list[DeviceRead | TelemetryRead | AnalyticsRead | PredictionRead]
) -> list[dict[str, str | float | int | datetime | bool]]:
    if AnalyticsRead in model_list or TelemetryRead in model_list:
        return [model.model_dump(exclude={"device_name", "device_location"}) for model in model_list]

    return [model.model_dump() for model in model_list]


def to_csv(model_list: list[DeviceRead | TelemetryRead | AnalyticsRead | PredictionRead]) -> StreamingResponse:
    data = _validate_model_list(model_list)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv")
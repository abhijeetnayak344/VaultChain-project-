from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Normalize DRF errors to a stable envelope for the React client."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    payload = response.data
    message = "Request failed"
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            message = detail
    elif isinstance(payload, list) and payload:
        message = str(payload[0])

    response.data = {
        "success": False,
        "error": {
            "code": getattr(response, "status_code", 500),
            "message": message,
            "details": payload,
        },
    }
    return response

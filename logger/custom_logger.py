from loguru import logger
import json
import sys

def custom_json_formatter(message, record):
    return json.dumps({
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "module": record["module"],
        "message": record["message"],
        "correlation_id": record["extra"].get("correlation_id", None),
    })

def configure_logging():
    logger.remove()
    logger.add(sys.stdout, format=custom_json_formatter, serialize=False)
    
import logging
import sys

import pytz
from config import app_config
from fastapi import FastAPI
from lifecycle import lifespan

logging.basicConfig(
    level=app_config.LOG_LEVEL,
    format=app_config.LOG_FORMAT,
    datefmt=app_config.LOG_DATEFORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

# 设置时区
if app_config.LOG_TZ:
    from datetime import datetime

    import pytz

    timezone = pytz.timezone(app_config.LOG_TZ)

    def time_converter(seconds):
        return datetime.utcfromtimestamp(seconds).astimezone(timezone).timetuple()

    for handler in logging.root.handlers:
        handler.formatter.converter = time_converter

app = FastAPI(lifespan=lifespan)


@app.get("/")
def index():
    return {"message": "Hello World"}

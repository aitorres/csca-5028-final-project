"""
Module-wide configuration for Analyzer.
"""

import logging
import os
import sys

import sentry_sdk

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(asctime)s %(levelname)s %(thread)d %(name)s] %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

environment = os.environ.get("ENVIRONMENT", "development")
if environment == "production":
    sentry_dsn = os.environ["SENTRY_DSN"]

    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        environment=environment,
    )

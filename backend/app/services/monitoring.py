from __future__ import annotations

import os


def init_monitoring() -> None:
    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    if not sentry_dsn:
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    environment = os.getenv("ENV", "development").lower()
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05"))

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        send_default_pii=False,
    )

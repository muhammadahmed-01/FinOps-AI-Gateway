"""Persistent Prometheus metrics server for Grafana scraping."""

from __future__ import annotations

import os
import sys
import time

from finops_gateway.config import load_settings
from finops_gateway.metrics import ensure_metrics_server


def main() -> None:
    load_settings()
    port = int(os.getenv("METRICS_PORT", "9464"))
    ensure_metrics_server(port)
    print(f"FinOps metrics server listening on http://0.0.0.0:{port}/metrics")
    print("Leave this running while you execute gateway queries.")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nShutting down metrics server.")
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Local HTTP API for printing D30 labels, with a docs/usage page at /.

Runs on 127.0.0.1 (this machine only) by default -- there's no
authentication, so only pass --host 0.0.0.0 if you understand that
anyone on the network could then trigger a print.
"""

from __future__ import annotations

import argparse

import serial
from flask import Flask, jsonify, request

from d30 import jobs
from d30.discovery import PortResolutionError
from d30.docs_page import render_docs_page

app = Flask(__name__)


class BadRequest(Exception):
    pass


def _float(value, default):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        raise BadRequest(f"expected a number, got {value!r}")


def _int(value, default):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise BadRequest(f"expected an integer, got {value!r}")


def _collect_params() -> dict:
    params: dict = {}
    if request.is_json:
        params.update(request.get_json(silent=True) or {})
    for key in request.values:
        params.setdefault(key, request.values[key])
    return params


def _run_print_job(params: dict) -> dict:
    mode = str(params.get("mode", "text")).strip().lower()
    com_port = params.get("com_port") or None
    length = _float(params.get("length"), None)
    count = _int(params.get("count"), 1)
    pause_ms = _float(params.get("pause_ms"), 250)

    if count < 1:
        raise BadRequest("count must be at least 1")
    if pause_ms < 0:
        raise BadRequest("pause_ms must be >= 0")

    if mode == "text":
        text = params.get("text")
        if not text:
            raise BadRequest("'text' is required for mode=text")
        used_port = jobs.print_text(
            str(text).replace("\\n", "\n"),
            port=com_port,
            length_mm=length,
            count=count,
            pause_s=pause_ms / 1000,
        )
        return {"mode": "text", "com_port": used_port, "count": count}

    if mode == "batch":
        batch = params.get("batch")
        best_before = params.get("best_before")
        if not batch or not best_before:
            raise BadRequest("'batch' and 'best_before' are required for mode=batch")
        used_port = jobs.print_batch(
            str(batch),
            str(best_before),
            port=com_port,
            length_mm=length if length is not None else 30,
            count=count,
            pause_s=pause_ms / 1000,
        )
        return {"mode": "batch", "com_port": used_port, "count": count}

    raise BadRequest(f"unknown mode {mode!r}, expected 'text' or 'batch'")


@app.after_request
def add_cors_headers(response):
    # Permissive by design: this is a local device bridge for a browser
    # page on the same machine, not a multi-tenant service.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/")
def docs():
    return render_docs_page(request.host_url)


@app.route("/api/print", methods=["GET", "POST", "PUT", "OPTIONS"])
def api_print():
    if request.method == "OPTIONS":
        return "", 204

    try:
        result = _run_print_job(_collect_params())
    except BadRequest as exc:
        return jsonify(status="error", message=str(exc)), 400
    except PortResolutionError as exc:
        return jsonify(status="error", message=str(exc)), 503
    except serial.SerialException as exc:
        return jsonify(status="error", message=f"Serial error: {exc}"), 502
    except Exception as exc:  # noqa: BLE001 -- surface unexpected errors to the caller
        return jsonify(status="error", message=f"Unexpected error: {exc}"), 500

    return jsonify(status="ok", **result), 200


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="interface to listen on (default: 127.0.0.1, this machine only)")
    parser.add_argument("--port", type=int, default=8787, help="HTTP port to listen on (default: 8787)")
    args = parser.parse_args()

    print(f"Docs: http://{args.host}:{args.port}/")
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

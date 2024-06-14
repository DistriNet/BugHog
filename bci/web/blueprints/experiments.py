import datetime
import json
import logging
import os
from urllib.parse import urlparse

import requests
from flask import Blueprint, make_response, render_template, request
from markupsafe import escape

from bci.web.page_parser import load_experiment_pages

ALLOWED_DOMAINS = [
    "leak.test",
    "a.test",
    "sub.a.test",
    "sub.sub.a.test",
    "b.test",
    "adition.com",
]

logger = logging.getLogger(__name__)
experiment_pages = load_experiment_pages("/app/experiments/pages", ALLOWED_DOMAINS)
exp = Blueprint("experiments", __name__, template_folder="/app/bci/web/templates")


@exp.before_request
def before_request():
    host = request.host.lower()
    if host not in ALLOWED_DOMAINS:
        logger.error(
            f"Host '{host}' is not supported by this framework. Supported hosts are {ALLOWED_DOMAINS}"
        )
        return f"Host '{host}' is not supported by this framework."


@exp.route("/")
def index():
    return f"This page is visited over <b>{request.scheme}</b>."


@exp.route("/report/", methods=["GET", "POST"])
def report_leak():
    leak = request.args.get("leak")
    if leak is not None:
        resp = make_response(
            render_template("cookies.html", title="Report", to_report=leak)
        )
    else:
        resp = make_response(
            render_template(
                "cookies.html", title="Report", to_report="Nothing to report"
            )
        )

    cookie_exp_date = datetime.datetime.now() + datetime.timedelta(weeks=4)
    resp.set_cookie("generic", "1", expires=cookie_exp_date)
    resp.set_cookie("secure", "1", expires=cookie_exp_date, secure=True)
    resp.set_cookie("httpOnly", "1", expires=cookie_exp_date, httponly=True)
    resp.set_cookie("lax", "1", expires=cookie_exp_date, samesite="lax")
    resp.set_cookie("strict", "1", expires=cookie_exp_date, samesite="strict")

    # Respond to collector on same IP
    # remote_ip = request.remote_addr
    remote_ip = request.headers.get("X-Real-IP")

    response_data = {
        "url": request.url,
        "method": request.method,
        "headers": dict(request.headers),
        "content": request.data.decode("utf-8"),
    }
    try:
        requests.post(f"http://{remote_ip}:5001/report/", json=response_data, timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"WARNING: Could not propagate request to collector at {remote_ip}:5001")

    return resp


@exp.route("/report/if/using/<string:protocol>")
def report_leak_if_using_http(protocol):
    """
    Forces request to /report/?leak=xxx if a request was received over a certain protocol.
    """
    leak = request.args.get("leak")
    if request.url.startswith(f"{protocol}://"):
        return "Redirect", 307, {"Location": f"https://adition.com/report/?leak={leak}"}
    else:
        return f"Request was not received over {protocol}", 200, {}


@exp.route("/report/if/<string:expected_header_name>")
def report_leak_if_present(expected_header_name: str):
    """
    Forces request to /report/?leak=xxx if a request header by name of expected_header_name was received.
    """
    if expected_header_name not in request.headers:
        return f"Header {expected_header_name} not found", 200, {"Allow-CSP-From": "*"}

    leak = request.args.get("leak")
    if leak is not None:
        return (
            "Redirect",
            307,
            {
                "Location": f"https://adition.com/report/?leak={leak}",
                "Allow-CSP-From": "*",
            },
        )
    else:
        return (
            "Redirect",
            307,
            {"Location": "https://adition.com/report/", "Allow-CSP-From": "*"},
        )


@exp.route(
    "/report/if/<string:expected_header_name>/contains/<string:expected_header_value>"
)
def report_leak_if_contains(expected_header_name: str, expected_header_value: str):
    """
    Forces request to /report/?leak=xxx if a request header by name of expected_header_name with value expected_header_value was received.
    """
    if expected_header_name not in request.headers:
        return f"Header {expected_header_name} not found", 200, {"Allow-CSP-From": "*"}
    elif expected_header_value not in request.headers[expected_header_name]:
        return (
            f"Header {expected_header_name} found, but expected value '{expected_header_value}' did not equal real value '{request.headers[expected_header_name]}'",
            200,
            {"Allow-CSP-From": "*"},
        )

    leak = request.args.get("leak")
    if leak is not None:
        return (
            "Redirect",
            307,
            {
                "Location": f"https://adition.com/report/?leak={leak}",
                "Allow-CSP-From": "*",
            },
        )
    else:
        return (
            "Redirect",
            307,
            {"Location": "https://adition.com/report/", "Allow-CSP-From": "*"},
        )


@exp.route("/<string:project>/<string:experiment>/<string:page>")
def custom_test_cases(project, experiment, page):
    host = urlparse(request.base_url).hostname
    path = os.path.join(project, experiment, page)

    experiment_pages_str = escape(json.dumps(experiment_pages, indent=4))
    if experiment_pages is None:
        return "Could not load any test cases", 404
    if host not in experiment_pages:
        return (
            f"Could not find domain '{host}'<br>Test cases:<br>{experiment_pages_str}",
            404,
        )
    if path not in experiment_pages[host]:
        return (
            f"Could not find path '{path}' for domain '{host}'<br>Test cases:<br>{experiment_pages_str}",
            404,
        )

    content = experiment_pages[host][path]["content"]
    status = 200  # Default value
    # resp = make_response(render_template("custom", content=content))
    headers = dict()
    if "headers" in experiment_pages[host][path]:
        for header in experiment_pages[host][path]["headers"]:
            if header["key"] == "status":
                status = header["value"]
            else:
                if header["key"] not in headers.keys():
                    headers[header["key"]] = list()
                headers[header["key"]].append(header["value"])
    # resp.headers = headers
    return content, status, headers

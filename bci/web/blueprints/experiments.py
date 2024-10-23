import datetime
import logging
import threading
import importlib.util
import sys

import requests
from flask import Blueprint, make_response, render_template, request, url_for

from bci.web.page_parser import load_experiment_pages

ALLOWED_DOMAINS = [
    "leak.test",
    "a.test",
    "sub.a.test",
    "sub.sub.a.test",
    "b.test",
    "sub.b.test",
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
def report():
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

    def send_report_to_collector():
        try:
            requests.post(f"http://{remote_ip}:5001/report/", json=response_data, timeout=5)
        except requests.exceptions.ConnectionError:
            logger.warning(f"WARNING: Could not propagate request to collector at {remote_ip}:5001")

    threading.Thread(target=send_report_to_collector).start()

    return resp


@exp.route("/report/if/scheme/<string:target_scheme>/")
def report_leak_if_using_http(target_scheme):
    """
    Triggers request to /report/ if a request was received over the specified `scheme`.
    """
    used_scheme = request.headers.get("X-Forwarded-Proto")
    params = get_all_bughog_GET_parameters(request)
    if used_scheme == target_scheme:
        return "Redirect", 307, {"Location": url_for("experiments.report", **params)}
    else:
        return f"Request was received over {used_scheme}, instead of {target_scheme}", 200, {}


@exp.route("/report/if/<string:expected_header_name>/")
def report_leak_if_present(expected_header_name: str):
    """
    Triggers request to /report/ if a request header by name of `expected_header_name` was received.
    """
    if expected_header_name not in request.headers:
        return f"Header {expected_header_name} not found", 200, {"Allow-CSP-From": "*"}

    params = get_all_bughog_GET_parameters(request)
    return (
        "Redirect",
        307,
        {
            "Location": url_for("experiments.report", **params),
            "Allow-CSP-From": "*",
        },
    )


@exp.route("/report/if/<string:expected_header_name>/contains/<string:expected_header_value>/")
def report_leak_if_contains(expected_header_name: str, expected_header_value: str):
    """
    Triggers request to /report/ if a request header `expected_header_name` with value `expected_header_value` was received.
    """
    if expected_header_name not in request.headers:
        return f"Header {expected_header_name} not found", 200, {"Allow-CSP-From": "*"}
    elif expected_header_value not in request.headers[expected_header_name]:
        return (
            f"Header {expected_header_name} found, but expected value '{expected_header_value}' was not found in the actual value '{request.headers[expected_header_name]}'",
            200,
            {"Allow-CSP-From": "*"},
        )

    params = get_all_bughog_GET_parameters(request)
    return (
        "Redirect",
        307,
        {
            "Location": url_for("experiments.report", **params),
            "Allow-CSP-From": "*",
        },
    )


@exp.route("/<string:project>/<string:experiment>/<string:directory>/")
def python_evaluation(project: str, experiment: str, directory: str):
    """
    Evaluates the python script and returns its result.
    """
    host = request.host.lower()

    module_name = f"{host}/{project}/{experiment}/{directory}"
    path = f"experiments/pages/{project}/{experiment}/{host}/{directory}/index.py"

    # Dynamically import the file
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module.main(request)


def get_all_bughog_GET_parameters(request):
    return {k: v for k, v in request.args.items() if k.startswith("bughog_")}

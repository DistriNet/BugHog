from flask import Request
from typing import Callable

def main(req: Request, report_leak: Callable[[], None]):
    if "leaked_secret" in req.url:
        report_leak()

    return {
        "agent": req.headers.get("User-Agent"),
        "cookies": req.cookies,
        "host": req.host,
        "path": req.path,
        "scheme": req.scheme,
        "url": req.url
    }

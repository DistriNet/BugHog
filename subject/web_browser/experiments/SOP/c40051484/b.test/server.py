from flask import Request
from typing import Callable

def main(req: Request, report_leak: Callable[[], None]):
    if req.method == 'POST' and req.cookies.get('my_name') == 'secret':
        return 'Leak', 307, {
            "Access-Control-Allow-Origin": "*",
            "Location": "https://a.test/report/?leak=c40051484"
        }

    return {
        "agent": req.headers.get("User-Agent"),
        "cookies": req.cookies,
        "host": req.host,
        "path": req.path,
        "scheme": req.scheme,
        "url": req.url
    }
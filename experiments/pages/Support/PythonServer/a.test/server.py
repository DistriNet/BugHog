from flask import Request

# Make sure that your file ends with '.py'

def main(req: Request):
    # TODO - implement your functionality and return a Flask response

    return {
        "agent": req.headers.get("User-Agent"),
        "cookies": req.cookies,
        "host": req.host,
        "path": req.path,
        "scheme": req.scheme,
        "url": req.url
    }

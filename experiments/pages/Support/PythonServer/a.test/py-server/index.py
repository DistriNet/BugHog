from flask import Request

def main(req: Request):
    # TODO - implement your functionality
    
    return {
        "agent": req.headers.get("User-Agent"),
        "cookies": req.cookies,
        "host": req.host,
        "path": req.path,
        "scheme": req.scheme,
        "url": req.url
    }
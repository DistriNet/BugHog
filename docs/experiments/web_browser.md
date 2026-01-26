# Web browser experiments

## Supported file types

The experiment server can technically serve virtually any file, but the following types are officially supported:

- `.html`
- `.css`
- `.js`
- `.xml`
- `.py`


## Available domain names

The following domain names are available for use in PoCs:
- `a.test`
- `sub.a.test`
- `sub.sub.a.test`
- `b.test`
- `sub.b.test`
- `leak.test`


## Available file parameters

Special parameters can be defined at the top of a file (placing them after the DOCTYPE declaration is allowed).
They must be included within comments.

Parameter comments must be written one line at a time.
Only single-line comments are supported for JavaScript files.

| **Parameter** | **Description** | **Default** |
|-|-|-|
| `Status` | HTTP response status code returned by the server. | `200` |
| `header_name`: `header_value` | Adds a custom HTTP header to the response. | / |
| `bughog_domain` | Domain from which the file should be served. If no `script.md` exists, the browser will navigate to `index.html` in the PoC root using this domain. | `a.test` |


### Example

The following example defines an `index.html` file that returns a 302 redirect to `https://leak.test`, and will be visited at the domain `b.test`.

```html
<!DOCTYPE html>
<!-- Status: 302 -->
<!-- Location: https://leak.test -->
<!-- bughog_domain: b.test -->
<html>
    <head>
    </head>
    <body>
        You should have been redirected.
    </body>
</html>
```

The following `script.js` file will be served with status code `202` and a Referrer-Policy header.

```js
// Status: 202
// Referrer-Policy: no-referrer
fetch("https://sub.a.test");
```

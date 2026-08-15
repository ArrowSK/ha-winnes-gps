# Contributing

Contributions are welcome, especially compatibility reports for additional WINNES/TKSTAR models that use the same mytkstar backend.

## Privacy rules for contributions

Never commit or attach real HAR files, cookies, passwords, tracker serials, backend IDs, vehicle registrations, exact coordinates, or unredacted API responses.

If a regression requires a fixture, construct a synthetic fixture with invented IDs, names, coordinates and timestamps. Preserve only the response structure needed to reproduce the parser behavior.

Do not add device enumeration, CAPTCHA bypass, credential scraping, or commands that can alter a tracker without first discussing the design and security implications.

## Checks

Run before opening a pull request:

```bash
python scripts/validate.py
python -m unittest discover -s tests
python -m compileall -q custom_components scripts tests
```

Keep the integration compatible with the minimum Home Assistant version declared in `hacs.json` unless a change explicitly raises that minimum.

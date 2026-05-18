from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib import parse, request

IMAGE_PATH_ARG_INDEX = 2


def main() -> None:
    """Post a local file to the development server without extra dependencies."""
    server_url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000/api/v1/frames'
    parsed = parse.urlparse(server_url)
    if parsed.scheme not in {'http', 'https'}:
        msg = f'Unsupported URL scheme: {parsed.scheme}'
        raise ValueError(msg)
    image_path = Path(sys.argv[IMAGE_PATH_ARG_INDEX]) if len(sys.argv) > IMAGE_PATH_ARG_INDEX else None
    payload = image_path.read_bytes() if image_path else b'smoke-frame'
    req = request.Request(  # noqa: S310
        server_url,
        data=payload,
        method='POST',
        headers={
            'Content-Type': 'image/jpeg',
            'X-Camera-Id': 'local-smoke',
        },
    )
    with request.urlopen(req, timeout=10) as res:  # noqa: S310
        body = json.loads(res.read().decode('utf-8'))
    sys.stdout.write(json.dumps(body, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()

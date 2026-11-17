"""Process entrypoint for Gunicorn and local development.

Render sets PORT. The process binds to 0.0.0.0 so the platform proxy can
reach it. Do not hardcode the listen port.
"""

import os

from webhook_monitor import create_app

app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=port, debug=debug)

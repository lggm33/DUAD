import os

from app import create_app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    debug = bool(app.config.get("DEBUG", False))
    app.run(host="0.0.0.0", port=port, debug=debug)



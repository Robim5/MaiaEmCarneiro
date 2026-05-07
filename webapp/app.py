""" aplicação Flask, o meu dashboard local (vista mensal) """

from __future__ import annotations

import os

from flask import Flask, render_template

from webapp.routes.dashboard import bp as dashboard_bp
from webapp.routes.repo_assets import bp as repo_assets_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(repo_assets_bp)

    @app.errorhandler(500)
    def server_error(_e):
        return (
            render_template(
                "error.html",
                title="Erro no servidor",
                message="Algo correu mal ao processar o pedido. Recarrega a página ou confirma o .env.",
            ),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host="127.0.0.1", port=port, debug=debug)

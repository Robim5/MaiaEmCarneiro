""" ficheiros do repositório servidos em URLs estáveis (tipo: /assets/logo.png)"""

from __future__ import annotations

from flask import Blueprint, abort, has_request_context, send_file, url_for

from webapp.config import LOGO_FILE

bp = Blueprint("repo_assets", __name__)


@bp.get("/assets/logo.png")
def logo_file():
    if not LOGO_FILE.is_file():
        abort(404)
    return send_file(LOGO_FILE, max_age=3600)


def logo_url() -> str | None:
    if not LOGO_FILE.is_file():
        return None
    if has_request_context():
        return url_for("repo_assets.logo_file")
    return "/assets/logo.png"

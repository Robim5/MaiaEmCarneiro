""" ficheiros estáticos fora da pasta webapp/static """

from __future__ import annotations

from flask import Blueprint, abort, has_request_context, send_file, url_for

from webapp.config import LOGO_FILE

bp = Blueprint("media", __name__)


@bp.get("/logo.png")
def logo():
    if not LOGO_FILE.is_file():
        abort(404)
    return send_file(LOGO_FILE, max_age=3600)


def logo_url() -> str | None:
    """
    URL absoluta a partir da raiz do site (/media/logo.png).
    Usa url_for para não depender do path da página (?m=...) nem de './' que alguns browsers tratam mal.
    """
    if not LOGO_FILE.is_file():
        return None
    if has_request_context():
        return url_for("media.logo")
    return "/media/logo.png"

"""Utilitaires partagés par les fonctions Vercel."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# rendre le paquet surf_forecast importable depuis /api
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reply(h: BaseHTTPRequestHandler, status: int, body: dict) -> None:
    data = json.dumps(body).encode()
    h.send_response(status)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)

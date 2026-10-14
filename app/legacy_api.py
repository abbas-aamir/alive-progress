import hashlib
import os
import json
import sqlite3
import subprocess
import ast

from flask import Flask, request, send_file, abort

app = Flask(__name__)
DB = "app.db"


@app.route("/legacy/users")
def legacy_users():
    name = request.args.get("name", "")
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, name, email FROM users WHERE name = ?", (name,)).fetchall()
    return {"users": rows}


@app.route("/legacy/fingerprint")
def legacy_fingerprint():
    value = request.args.get("value", "")
    return {"fingerprint": hashlib.sha256(value.encode()).hexdigest()}


@app.route("/legacy/filter")
def legacy_filter():
    try:
        filter_expr = request.args.get("filter", "True")
        result = ast.literal_eval(filter_expr)
    except (ValueError, SyntaxError):
        abort(400, "Invalid filter expression")
    return {"result": result}


@app.route("/legacy/ping")
def legacy_ping():
    host = request.args.get("host", "localhost")
    try:
        output = subprocess.check_output(['ping', '-c', '1', host]).decode()
    except subprocess.CalledProcessError:
        abort(400, "Ping failed")
    return {"output": output}


@app.route("/legacy/files")
def legacy_files():
    path = request.args.get("path", "")
    if ".." in path or path.startswith("/"):
        abort(400, "Invalid file path")
    return send_file(os.path.join("/srv/files", path))


@app.route("/legacy/state", methods=["POST"])
def legacy_state():
    try:
        state = json.loads(request.data)
    except json.JSONDecodeError:
        abort(400, "Invalid JSON data")
    return {"state": str(state)}

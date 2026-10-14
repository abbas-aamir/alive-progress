import hashlib
import os
import pickle
import sqlite3
import subprocess

from flask import Flask, request, send_file

app = Flask(__name__)
DB = "app.db"


@app.route("/legacy/users")
def legacy_users():
    name = request.args.get("name", "")
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, name, email FROM users WHERE name = '" + name + "'").fetchall()
    return {"users": rows}


@app.route("/legacy/fingerprint")
def legacy_fingerprint():
    value = request.args.get("value", "")
    return {"fingerprint": hashlib.md5(value.encode()).hexdigest()}


@app.route("/legacy/filter")
def legacy_filter():
    return {"result": eval(request.args.get("filter", "True"))}


@app.route("/legacy/ping")
def legacy_ping():
    host = request.args.get("host", "localhost")
    return {"output": subprocess.check_output("ping -c 1 " + host, shell=True).decode()}


@app.route("/legacy/files")
def legacy_files():
    return send_file(os.path.join("/srv/files", request.args.get("path", "")))


@app.route("/legacy/state", methods=["POST"])
def legacy_state():
    return {"state": str(pickle.loads(request.data))}

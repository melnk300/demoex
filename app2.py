import sqlite3

from flask import Flask, request, make_response, render_template, session, jsonify
from sqlite3 import connect, Row
import hashlib

app = Flask(__name__)
app.secret_key = "123456"


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@app.route("/api/register", methods=["POST"])
def register():
    with connect("instance/project.db") as db:
        cur = db.cursor()
        cur.row_factory = dict_factory
        body = request.json
        hashed_password = hashlib.sha256(body["password"].encode()).hexdigest()
        try:
            cur.execute("INSERT INTO users (name, tel, email, password) VALUES (?, ?, ?, ?)",
                        (body["name"], body["tel"], body["email"], hashed_password,))
            db.commit()
            user_id = cur.lastrowid
            session["user_id"] = user_id
            resp = jsonify({
                "name": body["name"],
                "role": 0
            })
            resp.status_code = 201
            cur.close()
            return resp
        except Exception as e:
            print(e)
            resp = make_response()
            resp.status_code = 409
            return resp


@app.route("/api/login", methods=["POST"])
def login():
    with connect("instance/project.db") as db:
        cur = db.cursor()
        cur.row_factory = dict_factory
        body = request.json
        hashed_password = hashlib.sha256(body["password"].encode()).hexdigest()

        cur.execute("SELECT id, name, password, role FROM users WHERE email = ?", (body["email"],))
        user = cur.fetchone()
        if user:
            if user["password"] == hashed_password:
                session["user_id"] = user["id"]
                cur.close()
                resp = jsonify({
                    "name": user["name"],
                    "role": user["role"]
                })
                resp.status_code = 200
                return resp
            else:
                resp = make_response()
                resp.status_code = 401
                cur.close()
                return resp
        else:
            resp = make_response()
            resp.status_code = 204
            cur.close()
            return resp


@app.route("/auth")
def auth_page():
    return render_template("auth.html")


@app.route("/")
def profile_page():
    return render_template("index.html")


@app.route("/api/data", methods=["GET"])
def get_data():
    with connect("instance/project.db") as db:
        if not session:
            return "401"
        user_id = session["user_id"]
        cur = db.cursor()
        cur.row_factory = dict_factory
        cur.execute("SELECT name, role FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()
        print(user)
        if user["role"] == 1:
            cur.execute("SELECT * FROM applications ORDER BY date, status")
        else:
            cur.execute("SELECT * FROM applications WHERE author_id = ? ORDER BY date, status", (user_id,))
        applications = cur.fetchall()
        if not applications:
            resp = jsonify({
                "user": user,
                "status": 404
            })
            resp.status_code = 404
            return resp
        else:
            return jsonify({
                "user": user,
                "applications": applications,
                "status": 200
            })


@app.route("/api/data/change", methods=["POST"])
def change_status():
    with connect("instance/project.db") as db:
        body = request.json
        cur = db.cursor()
        cur.row_factory = dict_factory
        cur.execute("UPDATE applications SET status = ? WHERE id = ?", (body["status"], body["id"],))
        db.commit()
        cur.close()
        return "201"


@app.route("/api/data", methods=["DELETE"])
def delete_application():
    with connect("instance/project.db") as db:
        body = request.json
        cur = db.cursor()
        cur.row_factory = dict_factory
        cur.execute("DELETE FROM applications WHERE id = ?", (body["id"],))
        db.commit()
        cur.close()
        return "201"


@app.route("/new", methods=["GET"])
def new_application_page():
    return render_template("new.html")


@app.route("/api/data/new", methods=["POST"])
def new_application():
    with connect("instance/project.db") as db:
        body = request.json
        cur = db.cursor()
        cur.row_factory = dict_factory
        if not session:
            return "401"
        user_id = session["user_id"]
        cur.execute("INSERT INTO applications (name, description, date, author_id) VALUES (?, ?, ?, ?)", (body["name"], body["description"], body["date"], user_id))
        db.commit()
        cur.close()
        return "201"


@app.route("/api/logout", methods=["DELETE"])
def logout_user():
    session.clear()
    return "200"


if __name__ == "__main__":
    app.run(debug=True)

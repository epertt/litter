import os
from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)

# index
@app.route("/")
def index():
    if session.get("user_id"):
        threads = get_user_threads()
        username = get_username()
        return render_template("index.html.j2", threads=threads, username=username)
    else:
        return redirect("/error/401")


# send message
@app.route("/thread/post", methods=["POST"])
def message_post():
    username = get_username()
    user_id = get_user_id()
    message = request.form["message"]

    sql = "INSERT INTO threads DEFAULT VALUES RETURNING id"
    result = db.session.execute(sql)
    db.session.commit()

    thread_id = result.first()[0]

    sql = "INSERT INTO messages (thread_id, user_id, message) VALUES (:thread_id, :user_id, :message)"
    db.session.execute(
        sql, {"thread_id": thread_id, "user_id": user_id, "message": message}
    )
    db.session.commit()
    return redirect("/")


# login, logout
@app.route("/login")
def login():
    return render_template("login.html.j2")


@app.route("/login/post", methods=["POST"])
def login_post():
    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT id, password FROM users WHERE username = :username"
    result = db.session.execute(sql, {"username": username}).first()

    user_id = result[0]
    password_hash = result[1]

    if check_password_hash(password_hash, password):
        session["user_id"] = user_id
        return redirect("/")
    else:
        return redirect("/error/401")


@app.route("/logout")
def logout():
    del session["user_id"]
    return render_template("logout.html.j2")


# register
@app.route("/register")
def register():
    return render_template("register.html.j2")


@app.route("/register/post", methods=["POST"])
def register_post():
    username = request.form["username"]
    password = request.form["password"]
    password = generate_password_hash(password)
    role = "user"

    sql = "INSERT INTO users (username, password, role) VALUES (:username, :password, :role)"
    db.session.execute(sql, {"username": username, "password": password, "role": role})
    db.session.commit()

    return redirect("/")


# errors
@app.route("/error/401")
def error_401():
    return render_template("401.html.j2")


# helper functions
def get_username():
    sql = "SELECT username FROM users WHERE id = :user_id"
    result = db.session.execute(sql, {"user_id": get_user_id()})
    return result.first()[0]


def get_user_id():
    return session.get("user_id", 0)


def get_user_threads():
    sql = "SELECT U.username, M.thread_id, M.message, EXTRACT(EPOCH FROM M.created_at)::INTEGER AS created_at, T.id FROM messages M, users U, threads T WHERE M.user_id = :user_id AND U.id = :user_id AND M.thread_id = T.id ORDER BY T.id DESC"
    result = db.session.execute(sql, {"user_id": get_user_id()})
    return result.fetchall()

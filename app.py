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

# index, displays user's own threads as well as threads from anyone they are following
@app.route("/")
def index():
    if user_id := session.get("user_id"):
        threads = get_user_threads(user_id)
        username = get_username(user_id)
        watched = get_watched_threads(user_id)
        return render_template(
            "index.html.j2", threads=threads, username=username, watched=watched
        )
    else:
        return redirect("/error/401")


# redirect to user's own page as seen by other users (for easier sharing)
@app.route("/user/me")
def ownpage():
    if user_id := session.get("user_id"):
        return redirect(f"/user/{user_id}")
    else:
        return redirect("/error/401")


# user pages
@app.route("/user/<int:id>")
def userpage(id):
    if get_username(id):
        # get id of user viewing page, then use that to find out if user is followed
        user_id = get_user_id()
        followed = is_followed(id, user_id)

        # get rest of relevant page info
        threads = get_user_threads(id)
        username = get_username(id)

        return render_template(
            "userpage.html.j2",
            threads=threads,
            username=username,
            userid=id,
            followed=followed,
        )
    else:
        return redirect("/error/404")


# follow, unfollow -- refactor to reduce code duplication?
@app.route("/follow/<int:id>")
def follow(id):
    if user_id := session.get("user_id"):
        if id == user_id:
            return redirect("/error/400")
        else:
            follow_id = id
            sql = "INSERT INTO watchers (user_id, watcher_id) VALUES (:follow_id, :user_id)"
            db.session.execute(sql, {"follow_id": follow_id, "user_id": user_id})
            db.session.commit()
            return redirect("/")
    else:
        return redirect("/error/401")


@app.route("/unfollow/<int:id>")
def unfollow(id):
    if user_id := session.get("user_id"):
        if id == user_id:
            return redirect("/error/400")
        else:
            follow_id = id
            sql = "DELETE FROM watchers WHERE user_id = :follow_id AND watcher_id = :user_id"
            db.session.execute(sql, {"follow_id": follow_id, "user_id": user_id})
            db.session.commit()
            return redirect("/")
    else:
        return redirect("/error/401")


# search
@app.route("/search/post", methods=["POST"])
def search_post():
    user_id = get_user_id()
    username = get_username(user_id)
    search_query = request.form["search"]

    return render_template(
        "search_results.html.j2",
        username=username,
        query=search_query,
        results=search_users(search_query),
    )


@app.route("/search/results", methods=["POST"])
def search_results(results):
    user_id = get_user_id()
    username = get_username(user_id)
    return render_template("search_results.html.j2", username=username, results=results)


# threads
@app.route("/thread/post", methods=["POST"])
def message_post():
    user_id = get_user_id()
    username = get_username(user_id)
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
    if user_id := session.get("user_id"):
        username = get_username(user_id)
        return render_template("401.html.j2", username=username)
    else:
        return render_template("401.html.j2")


@app.route("/error/404")
def error_404():
    if user_id := session.get("user_id"):
        username = get_username(user_id)
        return render_template("404.html.j2", username=username)
    else:
        return render_template("404.html.j2")


# helper functions
def get_user_id():
    return session.get("user_id", 0)


def get_username(user_id):
    sql = "SELECT username FROM users WHERE id = :user_id"
    result = db.session.execute(sql, {"user_id": user_id})
    if result.rowcount > 0:
        return result.first()[0]
    else:
        return False


def get_user_threads(user_id):

    sql = "\
        SELECT \
            U.username, \
            M.thread_id, \
            M.message, \
            EXTRACT(EPOCH FROM M.created_at)::INTEGER AS created_at, \
            T.id \
        FROM \
            messages M, \
            users U, \
            threads T \
        WHERE \
            M.user_id = :user_id \
        AND \
            U.id = :user_id \
        AND \
            M.thread_id = T.id \
        ORDER BY \
            T.id \
        DESC\
        "

    result = db.session.execute(sql, {"user_id": user_id})
    if result.rowcount >= 0:
        return result.fetchall()
    else:
        return False


def get_watched_threads(user_id):

    sql = "\
        SELECT \
            u.id, \
            u.username, \
            m.message, \
            EXTRACT(EPOCH FROM M.created_at)::INTEGER AS created_at, \
            w.watcher_id \
        FROM \
            users u \
        LEFT JOIN \
            messages m \
        ON \
            u.id = m.user_id \
        LEFT JOIN \
            watchers w \
        ON \
            u.id = w.user_id \
        WHERE \
            watcher_id = :user_id \
        ORDER BY \
            M.created_at \
        DESC\
        "

    result = db.session.execute(sql, {"user_id": user_id})
    if result.rowcount > 0:
        return result.fetchall()
    else:
        return False


def search_users(search_query):
    sql = """SELECT * FROM users WHERE username LIKE '%' || :search_query || '%'"""
    result = db.session.execute(sql, {"search_query": search_query})
    return result.fetchall()


def is_followed(user_id, watcher_id):
    # watcher_id is the user viewing the page; user_id in this case refers to the id of the user whose userpage is being viewed
    sql = "SELECT user_id FROM watchers WHERE user_id = :user_id AND watcher_id = :watcher_id"
    result = db.session.execute(sql, {"user_id": user_id, "watcher_id": watcher_id})

    # this can only really have either 0 (not following user) or 1 (following user) as results
    if result.rowcount == 1:
        return True
    else:
        return False

from config import app, db
from helpers import *
from flask import redirect, render_template, request, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import html, json

# think about this
#@app.before_request
#def before_request():

# index, displays user's own threads as well as threads from anyone they are following
@app.route("/")
def index():
    if user_id := session.get("user_id"):
        threads = get_user_threads(user_id)
        username = get_username(user_id)
        watched = get_watched_threads(user_id)

        return render_template(
            "index.html", threads=threads, username=username, watched=watched
        )
    else:
        return redirect("/login")


# user pages
@app.route("/user/<int:id>")
def userpage(id):
    if user_id := get_user_id():
        # get id of user viewing page, then use that to find out if user is followed
        followed = is_followed(id, user_id)

        # get rest of relevant page info
        threads = get_user_threads(id)
        username = get_username(user_id)

        return render_template(
            "userpage.html",
            threads=threads,
            username=username,
            viewed_username=get_username(id),
            viewed_id=id,
            viewer_id=user_id,
            is_followed=followed,
        )
    else:
        session["error"] = "you need to log in to view user pages."
        return redirect("/error/401")


# follow, unfollow -- redo this
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
        return redirect("/error/400")


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
        return redirect("/error/400")


# search
@app.route("/search/post", methods=["POST"])
def search_post():
    user_id = get_user_id()
    username = get_username(user_id)
    search_query = request.json["search"]
    results = search_users(search_query)
    data = []

    for result in results:
        data.append(result[0])

    return jsonify(data)


# threads
@app.route("/thread/<int:id>")
def thread(id):
    if thread_messages := get_thread_messages(id):
        user_id = get_user_id()
        return render_template(
            "thread.html",
            user_id=user_id,
            username=get_username(user_id),
            thread_messages=thread_messages,
            thread_id=id,
        )
    else:
        return redirect("/error/404")


@app.route("/thread/post", methods=["POST"])
def message_post():
    user_id = get_user_id()
    username = get_username(user_id)
    message = request.json["message"]

    if len(message) == 0:
        return redirect("/error/401")

    sql = "INSERT INTO threads DEFAULT VALUES RETURNING id"
    result = db.session.execute(sql)
    db.session.commit()

    thread_id = result.first()[0]

    sql = "INSERT INTO messages (thread_id, user_id, message, type) VALUES (:thread_id, :user_id, :message, :type)"
    db.session.execute(
        sql,
        {
            "thread_id": thread_id,
            "user_id": user_id,
            "message": message,
            "type": "thread",
        },
    )
    db.session.commit()
    return redirect("/")


@app.route("/thread/reply", methods=["POST"])
def thread_reply():
    user_id = get_user_id()
    reply = request.form["reply"]
    thread_id = request.form["thread_id"]

    if len(reply) == 0:
        return redirect("/error/401")

    sql = "INSERT INTO messages (thread_id, user_id, message, type) VALUES (:thread_id, :user_id, :message, :type)"
    db.session.execute(
        sql,
        {"thread_id": thread_id, "user_id": user_id, "message": reply, "type": "reply"},
    )
    db.session.commit()

    return redirect(f"/thread/{thread_id}")


# login, logout
@app.route("/login", defaults={"created_user": None})
@app.route("/login/<string:created_user>")
def login(created_user):
    return render_template("login.html", created_user=created_user)


@app.route("/login/post", methods=["POST"])
def login_post():
    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT id, password FROM users WHERE username = :username"
    result = db.session.execute(sql, {"username": username}).first()

    if result == None:
        return redirect("/error/401")
    else:
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
    return render_template("logout.html")


# register
@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register/post", methods=["POST"])
def register_post():
    username = request.form["username"]
    password = request.form["password"]
    role = "user"

    # don't allow usernames that need to be escaped
    username_escaped = html.escape(username)
    if not username == username_escaped:
        session[
            "error"
        ] = "username contained blacklisted characters. try an username consisting of letters, numbers, dashes or underscores."
        return redirect("/error/400")

    # don't allow empty usernames
    if len(username) == 0 or len(password) == 0:
        return redirect("/error/400")

    password = generate_password_hash(password)

    sql = "INSERT INTO users (username, password, role) VALUES (:username, :password, :role)"
    db.session.execute(sql, {"username": username, "password": password, "role": role})
    db.session.commit()

    return redirect(f"/login/{username}")


# errors (move these to another file?)
@app.route("/error/<int:errorcode>")
def error(errorcode):
    match errorcode:
        case 400:
            errortext = "bad request"
        case 401:
            errortext = "unauthorized (not logged in/not allowed to access page/wrong username or password)"
        case 404:
            errortext = "user or page doesn't exist"

    return (
        render_template(
            "error.html",
            moreinfo=session.pop("error", None),
            errorcode=errorcode,
            errortext=errortext,
        ),
        errorcode,
    )

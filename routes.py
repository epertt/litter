from config import app, db
from helpers import *
from flask import redirect, render_template, request, session, jsonify
import json

## think about this
# @app.before_request
# def before_request():

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


# follow if not following, unfollow otherwise
@app.route("/follow/<int:id>", methods=["POST"])
def follow(id):
    if user_id := authenticate(request.form["csrf_token"]):
        if id == user_id:
            return redirect("/error/400")
        else:
            if "follow" in request.form:
                follow_user(id, user_id)
            elif "unfollow" in request.form:
                unfollow_user(id, user_id)
            else:
                return redirect("/error/400")
            return redirect(f"/user/{id}")
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
    if user_id := authenticate(request.json["csrf_token"]):
        username = get_username(user_id)
        message = request.json["message"]

        post_thread_message(user_id, message)
        return redirect("/")
    else:
        return redirect("/error/401")


## consider another approach to getting thread_id
@app.route("/thread/reply", methods=["POST"])
def thread_reply():
    if user_id := authenticate(request.form["csrf_token"]):
        reply = request.form["reply"]
        thread_id = request.form["thread_id"]

        post_thread_reply(user_id, reply, thread_id)
        return redirect(f"/thread/{thread_id}")
    else:
        return "/error/401"


# login, logout
@app.route("/login", defaults={"created_user": None})
@app.route("/login/<string:created_user>")
def login(created_user):
    return render_template("login.html", created_user=created_user)


@app.route("/login/post", methods=["POST"])
def login_post():
    username = request.form["username"]
    password = request.form["password"]
    return login_user(username, password)


@app.route("/logout")
def logout():
    del session["user_id"]
    del session["csrf_token"]
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

    register_user(username, password, role)

    return redirect(f"/login/{username}")


# errors ## (move these to another file?)
@app.route("/error/<int:errorcode>")
def error(errorcode):
    match errorcode:
        case 400:
            errortext = "bad request"
        case 401:
            errortext = "unauthorized (not logged in/not allowed to access page/wrong username or password)"
        case 403:
            errortext = "forbidden"
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

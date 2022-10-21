from flask import session, redirect
from config import db, secrets
from werkzeug.security import check_password_hash, generate_password_hash
import html


def get_user_id():
    return session.get("user_id", 0)


def get_username(user_id):
    sql = "SELECT username FROM users WHERE id = :user_id"
    result = db.session.execute(sql, {"user_id": user_id})
    if result.rowcount > 0:
        return result.first()[0]
    else:
        return False


# the thread functions would ideally be a single function
def get_user_threads(user_id):

    sql = "\
        SELECT \
            u.id AS uid, \
            u.username, \
            m.user_id, \
            m.thread_id, \
            m.message, \
            m.type, \
            EXTRACT(EPOCH FROM m.created_at)::INTEGER AS created_at, \
            t.id \
        FROM \
            messages m, \
            users u, \
            threads t \
        WHERE \
            m.user_id = :user_id \
        AND \
            u.id = :user_id \
        AND \
            m.thread_id = t.id \
        AND \
            m.type = :type \
        ORDER BY \
            t.id \
        DESC\
        "

    result = db.session.execute(sql, {"user_id": user_id, "type": "thread"})
    if result.rowcount >= 0:
        return result.fetchall()
    else:
        return False


def get_watched_threads(user_id):

    sql = "\
        SELECT \
            u.id AS uid, \
            u.username, \
            m.thread_id, \
            m.message, \
            m.type, \
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
        AND \
            m.type = :type \
        ORDER BY \
            M.created_at \
        DESC\
        "

    result = db.session.execute(sql, {"user_id": user_id, "type": "thread"})
    if result.rowcount > 0:
        return result.fetchall()
    else:
        return False


def get_thread_messages(thread_id):

    sql = "\
    SELECT \
        u.id AS uid, \
        u.username, \
        m.thread_id, \
        m.message, \
        m.type, \
        EXTRACT(EPOCH FROM M.created_at)::INTEGER AS created_at \
    FROM \
        users u \
    LEFT JOIN \
        messages m \
    ON \
        u.id = m.user_id \
    WHERE \
        thread_id = :thread_id \
    ORDER BY \
       m.created_at \
    ASC\
    "

    result = db.session.execute(sql, {"thread_id": thread_id})
    if result.rowcount > 0:
        result = result.fetchall()
        return result
    else:
        return False


def search_users(search_query):
    sql = """SELECT row_to_json(r.*) FROM (SELECT id, username, (EXTRACT(EPOCH FROM created_at)::INTEGER) AS created_at FROM users WHERE username LIKE '%' || :search_query || '%') r ORDER BY created_at DESC"""
    result = db.session.execute(sql, {"search_query": search_query})
    return result.fetchall()


def is_followed(user_id, watcher_id):
    # watcher_id is the user viewing the page; user_id in this case refers to the id of the user whose userpage is being viewed
    sql = "SELECT user_id FROM watchers WHERE user_id = :user_id AND watcher_id = :watcher_id"
    result = db.session.execute(sql, {"user_id": user_id, "watcher_id": watcher_id})

    # no rows found with matching user_id and watcher_id means watcher_id is not followind user_id
    if result.rowcount == 0:
        return False
    else:
        return True


def csrf_check(token):
    if session.get("csrf_token") == token:
        return True
    else:
        return False


def follow_user(follow_id, user_id):
    sql = "INSERT INTO watchers (user_id, watcher_id) VALUES (:follow_id, :user_id)"
    db.session.execute(sql, {"follow_id": follow_id, "user_id": user_id})
    db.session.commit()


def unfollow_user(follow_id, user_id):
    sql = "DELETE FROM watchers WHERE user_id = :follow_id AND watcher_id = :user_id"
    db.session.execute(sql, {"follow_id": follow_id, "user_id": user_id})
    db.session.commit()


def post_thread_message(user_id, message):
    if len(message) == 0 or len(message) > 500:
        session[
            "error"
        ] = "message was too long (more than 500 characters) or too short (less than 1 character)"
        return redirect("/error/400")

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


def post_thread_reply(user_id, reply, thread_id):
    if len(reply) == 0 or len(reply) > 500:
        session[
            "error"
        ] = "message was too long (more than 500 characters) or too short (less than 1 character)"
        return redirect("/error/400")

    sql = "INSERT INTO messages (thread_id, user_id, message, type) VALUES (:thread_id, :user_id, :message, :type)"
    db.session.execute(
        sql,
        {
            "thread_id": thread_id,
            "user_id": user_id,
            "message": reply,
            "type": "reply",
        },
    )
    db.session.commit()


def register_user(username, password, role):
    # don't allow usernames that need to be escaped
    username_escaped = html.escape(username)
    if not username == username_escaped:
        session[
            "error"
        ] = "username contained blacklisted characters. try a username consisting of letters, numbers, dashes or underscores."
        return redirect("/error/400")

    # don't allow empty usernames and put at least some limits on username/password length
    if (
        len(username) == 0
        or len(password) == 0
        or len(username) > 30
        or len(password) > 500
    ):
        session["error"] = "username or password too long or too short."
        return redirect("/error/400")

    password = generate_password_hash(password)

    sql = "INSERT INTO users (username, password, role) VALUES (:username, :password, :role)"
    db.session.execute(sql, {"username": username, "password": password, "role": role})
    db.session.commit()


def login_user(username, password):
    sql = "SELECT id, password FROM users WHERE username = :username"
    result = db.session.execute(sql, {"username": username}).first()

    if result == None:
        session["error"] = "wrong username or password."
        return redirect("/error/401")
    else:
        user_id = result[0]
        password_hash = result[1]

        if check_password_hash(password_hash, password):
            session["user_id"] = user_id
            session["csrf_token"] = secrets.token_hex(16)
            return redirect("/")
        else:
            return redirect("/error/401")

def authenticate(token):
    if csrf_check(token):
        return get_user_id()
    else:
        return False
from flask import session
from config import db


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

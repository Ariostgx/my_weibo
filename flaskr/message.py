from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash


from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('message', __name__, url_prefix='/message')


def sort_by_creat_time(x):
    try:
        res = x['recent_chat']
    except KeyError:
        res = x['dated']
    return res


def message_with_sb(other_id):
    db = get_db()
    send_message = db.execute(
        'SELECT *'
        ' FROM message'
        ' WHERE sender_id = ? and receiver_id = ?'
        ' ORDER BY dated DESC',
        (g.user['id'], other_id)
    ).fetchall()

    receive_message = db.execute(
        'SELECT *'
        ' FROM message'
        ' WHERE sender_id = ? and receiver_id = ?'
        ' ORDER BY dated DESC',
        (other_id, g.user['id'])
    ).fetchall()

    not_read = 0
    for i in receive_message:
        if i['checked'] == 0:
            not_read += 1

    if len(send_message) == 0:
        recent_chat = receive_message[0]['dated']
        recent_message = receive_message[0]
    elif len(receive_message) == 0:
        recent_chat = send_message[0]['dated']
        recent_message = send_message[0]
    else:
        if send_message[0]['dated'] > receive_message[0]['dated']:
            recent_message = send_message[0]
            recent_chat = send_message[0]['dated']
        else:
            recent_message = receive_message[0]
            recent_chat = send_message[0]['dated']

    return send_message, receive_message, not_read, recent_chat, recent_message


@bp.route('/all')
@login_required
def message_index():
    db = get_db()
    user_id = g.user['id']
    send_to = db.execute(
        'SELECT receiver_id as id'
        ' FROM message'
        ' WHERE sender_id = ?'
        ' ORDER BY dated DESC',
        (user_id, )
    ).fetchall()

    receive_from = db.execute(
        'SELECT sender_id as id'
        ' FROM message'
        ' WHERE receiver_id = ?'
        ' ORDER BY dated DESC',
        (user_id, )
    ).fetchall()

    inter_user = []
    for i in send_to:
        inter_user.append(i['id'])
    for i in receive_from:
        inter_user.append(i['id'])
    inter_user = set(inter_user)
    inter_user_message = []
    for i in inter_user:
        inter_user_name = db.execute(
            'SELECT username as inter_user_name'
            ' FROM user'
            ' WHERE id = ?',
            (i, )
        ).fetchone()['inter_user_name']

        _, _, not_read, recent_chat, recent_message = message_with_sb(i)
        user = {'message': recent_message, 'not_read': not_read,
                'recent_chat': recent_chat, 'inter_user_name': inter_user_name,
                'inter_user_id': i}
        inter_user_message.append(user)

    inter_user_message = sorted(inter_user_message, key=sort_by_creat_time, reverse=True)
    return render_template('message/index.html', user_messages=inter_user_message)


@bp.route('/chat_with/<int:user_id>/all')
@login_required
def show_message_with_sb(user_id):
    db = get_db()
    send_message, receive_message, not_read, recent_chat, _ = message_with_sb(user_id)
    message = send_message + receive_message
    message = sorted(message, key=sort_by_creat_time, reverse=True)
    user = db.execute(
        'SELECT *'
        ' FROM user'
        ' WHERE id = ?',
        (user_id, )
    ).fetchone()

    db.execute(
        'UPDATE message SET checked = ?'
        ' WHERE receiver_id = ? and sender_id = ?',
        (1, g.user['id'], user_id)
    )

    return render_template('message/showMessageWithUser.html',
                           messages=message, user=user,
                           not_read=not_read)


@bp.route('/send_to/<int:send_to_id>/<string:send_to_name>', methods=('GET', 'POST'))
@login_required
def create(send_to_id, send_to_name):
    if request.method == 'POST':
        context = request.form['body']
        error = None

        if not context:
            error = 'Context is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO message(sender_id, receiver_id, context)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], send_to_id, context)
            )

            db.commit()
            return redirect(url_for('message.show_message_with_sb', user_id=send_to_id))

    return render_template('message/create.html', send_to_name=send_to_name)


@bp.route('/send_message', methods=('GET', 'POST'))
@login_required
def create_nd_way():
    if request.method == 'POST':
        username = request.form['username']
        context = request.form['body']
        error = None

        if not context:
            error = 'Context is required.'

        if not username:
            error = 'Username is required.'

        send_to_id = get_db().execute(
            ' SELECT id'
            ' FROM user'
            ' WHERE username = ?',
            (username,)
        ).fetchone()

        if send_to_id is None:
            error = 'No user named ' + username
        else:
            send_to_id = send_to_id['id']

        if error is not None:
            flash(error)

        else:
            db = get_db()
            cur = db.cursor()

            cur.execute(
                'INSERT INTO message(sender_id, receiver_id, context)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], send_to_id, context)
            )

            db.commit()
            return redirect(url_for('message.show_message_with_sb', user_id=send_to_id))

    return render_template('message/create_nd_way.html')


@bp.route('/send_to/<string:send_to_name>', methods=('GET', 'POST'))
@login_required
def create_rd_way(send_to_name):
    if request.method == 'POST':
        context = request.form['body']
        error = None

        if not context:
            error = 'Context is required.'

        send_to_id = get_db().execute(
            ' SELECT id'
            ' FROM user'
            ' WHERE username = ?',
            (send_to_name,)
        ).fetchone()

        if send_to_id is None:
            error = 'No user named ' + send_to_name
        else:
            send_to_id = send_to_id['id']

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO message(sender_id, receiver_id, context)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], send_to_id, context)
            )

            db.commit()
            return redirect(url_for('message.show_message_with_sb', user_id=send_to_id))

    return render_template('message/create_rd_way.html', send_to_name=send_to_name)

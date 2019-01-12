import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        birthday = request.form['birthday']
        email = request.form['email']
        gender = request.form['gender']
        telephone = request.form['telephone']
        introduction = request.form['introduction']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password, birthday, email,'
                'gender, telephone, introduction) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (username, generate_password_hash(password), birthday,
                 email, gender, telephone, introduction)
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('blog.index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

        leader_row = db.execute(
            'SELECT f.leader_id as id'
            ' FROM follower f'
            ' Where f.follower_id = ?',
            (user_id,)
        ).fetchall()
        leader = []
        for i in leader_row:
            leader.append(i['id'])
        g.leader = leader

        fork_row = db.execute(
            'SELECT b.id as id, b.ori_blog_id as ori_blog_id'
            ' FROM blog b JOIN user_blog u_b on u_b.blog_id = b.id'
            ' Where u_b.user_id = ?',
            (user_id,)
        ).fetchall()
        fork = []
        for i in fork_row:
            if i['ori_blog_id'] != -1:
                fork.append(i['ori_blog_id'])
        g.fork = fork

        not_read = db.execute(
            'SELECT *'
            ' FROM message'
            ' Where receiver_id = ? and checked = 0',
            (user_id,)
        ).fetchall()
        g.not_read = len(not_read)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


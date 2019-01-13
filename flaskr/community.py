from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.blog import get_user_and_forks, get_user_and_blogs, sort_by_creat_time
from . import blog


bp = Blueprint('community', __name__, url_prefix='/community')


@bp.route('/all')
def community_index():
    db = get_db()
    communities = db.execute(
        'SELECT theme, description, key_word, id, dated'
        ' FROM community'
        ' ORDER BY dated DESC'
    ).fetchall()

    return render_template('community/index.html', communities=communities)


@bp.route('/register', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        theme = request.form['theme']
        description = request.form['description']
        key_word = request.form['key_word']

        db = get_db()
        error = None

        if not theme:
            error = 'theme is required.'
        elif db.execute(
            'SELECT id FROM community WHERE theme = ?', (theme,)
        ).fetchone() is not None:
            error = 'Community {} is already registered.'.format(theme)

        if not description:
            description = 'Not description yet'
        db = db.cursor()
        if error is None:
            db.execute(
                'INSERT INTO community (theme, description, key_word)'
                ' VALUES (?, ?, ?)',
                (theme, description, key_word)
            )
            get_db().commit()
            last_id = db.lastrowid
            return redirect(url_for('community.show_community', community_id=last_id))

        flash(error)

    return render_template('community/create.html')


@bp.route('/detail/<int:community_id>')
def show_community(community_id):
    db = get_db()
    community = db.execute(
        'SELECT theme, description, key_word, id, dated'
        ' FROM community'
        ' WHERE id = ?',
        (community_id, )
    ).fetchone()

    users = db.execute(
        'SELECT user_id as id, dated'
        ' FROM member'
        ' WHERE community_id = ?'
        ' ORDER BY dated DESC',
        (community_id, )
    ).fetchall()

    have_join = 0
    if g.user is not None:
        if db.execute(
            'SELECT * FROM member WHERE user_id = ? and community_id = ?',
            (g.user['id'], community_id)
        ).fetchone() is not None:
            have_join = 1

    users_id = []
    for i in users:
        users_id.append(i['id'])
        i['username'] = db.execute(
            'SELECT username FROM user WHERE id = ?',
            (i['id'], )).fetchone()['username']

    blogs = []
    forks = []
    for user in users_id:
        _, blog_i, _, _ = get_user_and_blogs(user)
        _, fork_i, _, _ = get_user_and_forks(user)
        blogs = blogs + blog_i
        forks = forks + fork_i

    blogs = blogs + forks
    blogs = sorted(blogs, key=sort_by_creat_time, reverse=True)
    users = users[:3]
    return render_template('community/showCommunity.html',
                           community=community, users=users,
                           blogs=blogs, have_join=have_join)


# show users in the community
@bp.route('/members/<int:community_id>')
def show_users(community_id):
    db = get_db()
    users = db.execute(
        'SELECT user_id as id, dated'
        ' FROM member'
        ' WHERE community_id = ?'
        ' ORDER BY dated DESC',
        (community_id,)
    ).fetchall()

    for i in users:
        i['username'] = db.execute(
            'SELECT username FROM user WHERE id = ?',
            (i['id'], )).fetchone()['username']

    community = db.execute(
        'SELECT theme'
        ' FROM community'
        ' WHERE id = ?',
        (community_id, )
    ).fetchone()

    return render_template('community/showUsers.html',
                           users=users, theme=community['theme'])


@bp.route('/join/<int:community_id>')
@login_required
def join_community(community_id):
    db = get_db()

    db.execute(
        'INSERT INTO member (user_id, community_id)'
        ' VALUES (?, ?)',
        (g.user['id'], community_id))
    db.commit()
    return redirect(url_for('community.show_community', community_id=community_id))


@bp.route('/leave/<int:community_id>')
@login_required
def leave_community(community_id):
    db = get_db()

    db.execute(
        'DELETE FROM member WHERE user_id=? and community_id=?',
        (g.user['id'], community_id))
    db.commit()
    return redirect(url_for('community.show_community', community_id=community_id))


@bp.route('/search/', methods=('GET', 'POST'))
@login_required
def search():
    if request.method == 'POST':
        name = request.form['title']

        db = get_db()
        name = '%' + name + '%'
        communities = db.execute(
            'SELECT *'
            ' FROM community'
            ' Where theme like ?',
            (name,)
        ).fetchall()
        theme = name[1:-1]

        return render_template('community/show_search_res.html',
                               communities=communities, context=theme)

    return render_template('community/search.html')


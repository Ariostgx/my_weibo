from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.comment import get_comments_on_blog

bp = Blueprint('blog', __name__)


def sort_by_creat_time(x):
    try:
        res = x['fork_time']
    except IndexError:
        res = x['dated']

    return res


@bp.route('/')
def index():
    db = get_db()
    blogs = db.execute(
        'SELECT b.id, b.dated as dated, context, u.id as author_id, username'
        ' FROM user u JOIN user_blog u_b on u.id = u_b.user_id JOIN blog b on u_b.blog_id = b.id'
        ' ORDER BY dated DESC'
    ).fetchall()

    forks = db.execute(
        'SELECT b.id as id, f.dated as fork_time, b.dated as dated,'
        ' b.context as context, u2.id as author_id, u2.username as username, '
        ' u.username as fork_username'
        ' FROM fork f JOIN user u ON f.user_id = u.id JOIN blog b on f.blog_id = b.id'
        ' JOIN user_blog u_b on b.id=u_b.blog_id JOIN user u2 ON u2.id = u_b.user_id'
    ).fetchall()

    blogs = blogs + forks
    blogs = sorted(blogs, key=sort_by_creat_time, reverse=True)

    return render_template('blog/index.html', blogs=blogs)


@bp.route('/error')
def not_implement():
    return render_template('blog/NotImplement.html')


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
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
                'INSERT INTO blog(context)'
                ' VALUES (?)',
                (context, )
            )
            blog_id = cur.lastrowid
            cur.execute(
                'INSERT INTO user_blog(user_id, blog_id)'
                ' VALUES (?, ?)',
                (g.user['id'], blog_id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_blog(id, check_author=True):
    blog = get_db().execute(
        'SELECT b.id, b.dated as dated, context, '
        'u.id as author_id, username'
        ' FROM blog b JOIN user_blog u_b ON b.id = u_b.blog_id JOIN user u ON u_b.user_id=u.id'
        ' WHERE b.id = ?',
        (id,)
    ).fetchone()

    if blog is None:
        abort(404, "Blog id {0} doesn't exist.".format(id))

    if check_author and blog['author_id'] != g.user['id']:
        abort(403)

    return blog


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    blog = get_blog(id)

    if request.method == 'POST':
        context = request.form['body']
        error = None

        if not context:
            error = 'Context is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE blog SET context = ?'
                ' WHERE id = ?',
                (context, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', blog=blog)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    db.execute('DELETE FROM blog WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:blog_id>/blog')
@login_required
def show_blog(blog_id):
    blog = get_blog(blog_id, check_author=False)
    comments = get_comments_on_blog(blog_id)
    return render_template('blog/showBlog.html', blog=blog, comments=comments)


@bp.route('/friends/')
@login_required
def friends_blog():
    db = get_db()
    blogs = []
    forks = []
    for leader in g.leader:
        blogs_i = db.execute(
            'SELECT b.id, b.dated as dated, context, u.id as author_id, username'
            ' FROM user u JOIN user_blog u_b on u.id = u_b.user_id JOIN blog b on u_b.blog_id = b.id'
            ' WHERE u.id = ?'
            ' ORDER BY dated DESC',
            (leader, )
        ).fetchall()

        forks_i = db.execute(
            'SELECT b.id as id, f.dated as fork_time, b.dated as dated,'
            ' b.context as context, u2.id as author_id, u2.username as username, '
            ' u.username as fork_username'
            ' FROM fork f JOIN user u ON f.user_id = u.id JOIN blog b on f.blog_id = b.id'
            ' JOIN user_blog u_b on b.id=u_b.blog_id JOIN user u2 ON u2.id = u_b.user_id'
            ' WHERE u.id = ?'
            ' ORDER BY dated DESC',
            (leader, )
        ).fetchall()
        blogs = blogs + blogs_i
        forks = forks + forks_i

    blogs = blogs + forks
    blogs = sorted(blogs, key=sort_by_creat_time, reverse=True)

    return render_template('blog/index.html', blogs=blogs)


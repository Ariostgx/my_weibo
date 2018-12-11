from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.user import get_user
from flaskr.blog import get_blog, get_comments_on_blog


bp = Blueprint('fork', __name__, url_prefix='/fork')


def get_fork(user_id, blog_id, check_author=True):
    blog = get_db().execute(
        'SELECT b.id as id, b.dated as dated, f.dated as fork_time,'
        ' b.context u2.id as author_id, abstract, u2.username as username'
        ' u.username as fork_name'
        ' FROM user b JOIN fork f ON b.id = f.blog_id JOIN user u on u.id = f.user_id'
        ' JOIN user_blog u_b ON u_b.blog_id = b.id JOIN user u2 ON u2.id = u_b.user_id'
        ' WHERE b.id = ?and u.id=?',
        (blog_id, user_id)
    ).fetchone()

    if blog is None:
        abort(404, "blog id {0} doesn't exist.".format(id))

    if check_author and blog['author_id'] != g.user['id']:
        abort(403)

    return blog


@bp.route('/<int:blog_id>/create', methods=('GET', 'POST'))
@login_required
def create(blog_id):
    db = get_db()
    db.execute(
        'INSERT INTO fork (blog_id, user_id)'
        ' VALUES (?, ?)',
        (blog_id, g.user['id']))
    db.commit()
    g.fork.append(blog_id)

    return redirect(url_for('blog.show_blog', blog_id=blog_id))


@bp.route('/<int:blog_id>/delete')
@login_required
def delete(blog_id):
    db = get_db()
    db.execute('DELETE FROM fork WHERE blog_id = ? and user_id = ?',
               (blog_id, g.user['id']))
    db.commit()
    g.fork.remove(blog_id)
    return redirect(url_for('blog.show_blog', blog_id=blog_id))


@bp.route('/<int:user_id>/<int:blog_id>/')
@login_required
def show_fork(user_id, blog_id):
    user = get_user(user_id)
    blog = get_fork(user_id=user_id, blog_id=blog_id, check_author=False)
    comments = get_comments_on_blog(blog_id)
    return render_template('fork/showFork.html', user=user, blog=blog, comments=comments)


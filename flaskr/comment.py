from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from . import blog


bp = Blueprint('comment', __name__, url_prefix='/comment')


@bp.route('/create/<int:blog_id>/blog', methods=('GET', 'POST'))
@login_required
def create_comment_blog(blog_id):
    if request.method == 'POST':
        context = request.form['body']
        error = None

        if error is not None:
            flash(error)
        else:

            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO comment (user_id, blog_id, context)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], blog_id, context)
            )

            db.commit()
            return redirect(url_for('blog.show_blog', blog_id=blog_id))

    return render_template('comment/create.html')


@bp.route('/create/<int:blog_id>/<int:user_id>fork', methods=('GET', 'POST'))
@login_required
def create_comment_fork(blog_id, user_id):
    if request.method == 'POST':
        context = request.form['body']
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO comment (user_id, blog_id, context)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], blog_id, context)
            )

            db.commit()
            return redirect(url_for('fork.show_fork', user_id=user_id, blog_id=blog_id))

    return render_template('comment/create.html')


def get_comments_on_blog(blog_id, num_comment=-1):
    comments = get_db().execute(
        'SELECT c.dated as dated, c.context as context,'
        ' u.username as username, u.id as author_id,'
        ' c.user_id as user_id, c.blog_id as blog_id'
        ' FROM blog b  JOIN comment c on b.id = c.blog_id'
        ' JOIN user u ON u.id = c.user_id'
        ' WHERE b.id = ?'
        ' ORDER BY dated DESC',
        (blog_id,)
    ).fetchall()

    if num_comment != -1:
        if num_comment < len(comments):
            num_comment = len(comments)
        comments = comments[:num_comment]

    if comments is None:
        return ['Here no comment']

    return comments


def get_comment(user_id, blog_id, dated, check_author=False):
    comment = get_db().execute(
        'SELECT u.username as username, c.dated as dated, context, u.id as author_id,'
        ' c.user_id as user_id, c.blog_id as blog_id'
        ' FROM comment c JOIN user u ON c.user_id = u.id'
        ' WHERE c.user_id = ? and c.blog_id = ? and c.dated = ?',
        (user_id, blog_id, dated)
    ).fetchone()

    if comment is None:
        abort(404, "Comment id {0} doesn't exist.".format(id))

    if check_author and comment['author_id'] != g.user['id']:
        abort(403)

    return comment


@bp.route('/<int:user_id>/<int:blog_id>/<string:dated>/detail')
@login_required
def show_comment(user_id, blog_id, dated):
    comment = get_comment(user_id, blog_id, dated, check_author=False)
    return render_template('comment/showComment.html', comment=comment)


@bp.route('/<int:user_id>/<int:blog_id>/<string:dated>', methods=('GET', 'POST'))
@login_required
def update(user_id, blog_id, dated):
    comment = get_comment(user_id, blog_id, dated)

    if request.method == 'POST':
        context = request.form['body']
        error = None

        if not context:
            error = 'Body is required.'

        if error is not None:
            flash(error)
        else:

            db = get_db()
            db.execute(
                'UPDATE comment SET context = ?'
                ' WHERE user_id = ? and blog_id = ? and dated = ?',
                (context, user_id, blog_id, dated)
            )
            db.commit()
            return redirect(url_for('blog.show_blog', blog_id=blog_id))

    return render_template('comment/update.html', comment=comment)


@bp.route('/<int:user_id>/delete_comment', methods=('POST',))
@login_required
def delete(user_id, blog_id, dated):
    db = get_db()
    db.execute('DELETE FROM comment'
               ' WHERE user_id = ? and blog_id = ? and dated = ?', (user_id, blog_id, dated))
    db.commit()
    return redirect(url_for('blog.index'))




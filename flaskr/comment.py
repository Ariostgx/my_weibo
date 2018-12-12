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
                'INSERT INTO comment (context)'
                ' VALUES (?)',
                (context, )
            )
            c_id = cur.lastrowid

            cur.execute(
                'INSERT INTO blog_comment (blog_id, comment_id)'
                ' VALUES (?, ?)',
                (blog_id, c_id)
            )

            cur.execute(
                'INSERT INTO user_comment (user_id, comment_id)'
                ' VALUES (?, ?)',
                (g.user['id'], c_id)
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
                'INSERT INTO comment (context)'
                ' VALUES (?)',
                (context, )
            )

            c_id = cur.lastrowid

            cur.execute(
                'INSERT INTO blog_comment (blog_id, comment_id)'
                ' VALUES (?, ?)',
                (blog_id, c_id)
            )

            cur.execute(
                'INSERT INTO user_comment (user_id, comment_id)'
                ' VALUES (?, ?)',
                (g.user['id'], c_id)
            )
            db.commit()
            return redirect(url_for('fork.show_fork', user_id=user_id, blog_id=blog_id))

    return render_template('comment/create.html')


def get_comments_on_blog(blog_id):
    comments = get_db().execute(
        'SELECT c.id as id, c.dated as dated, c.context as context,'
        ' u.username as username, u.id as author_id'
        ' FROM blog b  JOIN blog_comment b_c on b.id = b_c.blog_id'
        ' JOIN comment c ON b_c.comment_id = c.id JOIN user_comment u_c ON c.id=u_c.comment_id'
        ' JOIN user u ON u.id = u_c.user_id'
        ' WHERE b.id = ?'
        ' ORDER BY dated DESC',
        (blog_id,)
    ).fetchall()

    if comments is None:
        return ['Here no comment']

    return comments


def get_comment(comment_id, check_author=False):
    comment = get_db().execute(
        'SELECT c.id, u.username as username, c.dated as dated, context, u.id as author_id'
        ' FROM comment c JOIN user_comment u_c ON c.id = u_c.comment_id'
        ' JOIN user u ON u_c.user_id = u.id'
        ' WHERE c.id = ?',
        (comment_id,)
    ).fetchone()

    if comment is None:
        abort(404, "Comment id {0} doesn't exist.".format(id))

    if check_author and comment['author_id'] != g.user['id']:
        abort(403)

    return comment


@bp.route('/<int:comment_id>/update', methods=('GET', 'POST'))
@login_required
def update(comment_id):
    comment = get_comment(comment_id)

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
                ' WHERE id = ?',
                (context, comment_id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('comment/update.html', comment=comment)


@bp.route('/<int:comment_id>/delete', methods=('POST',))
@login_required
def delete(comment_id):
    db = get_db()
    db.execute('DELETE FROM comment WHERE id = ?', (comment_id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:comment_id>/detail')
@login_required
def show_comment(comment_id):
    comment = get_comment(comment_id, check_author=False)
    return render_template('comment/showComment.html', comment=comment)

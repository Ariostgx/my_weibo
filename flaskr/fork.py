from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.user import get_user
from flaskr.blog import get_comments_on_blog


bp = Blueprint('fork', __name__, url_prefix='/forward')
fork_comment_default = '转发了微博'
fork_comment_maxlength = 140  # -1 means no limitation


def get_forward(user_id, blog_id, check_author=True):
    db = get_db()
    blog = db.execute(
        'SELECT b.id as id, b.dated as fork_time, '
        'b.context as fork_comment, u.username as fork_name,'
        'u.id as fork_id, b.ori_blog_id as ori_blog_id'
        ' FROM blog b JOIN user_blog u_b on b.id = u_b.blog_id'
        ' JOIN user u ON u.id = u_b.user_id '
        'WHERE u.id = ? and b.id = ?',
        (user_id, blog_id)
    ).fetchone()

    if blog is None:
        abort(404, "blog id {0} doesn't exist.".format(id))

    ori_blog = db.execute(
        'SELECT b.id as ori_id, b.dated as dated, '
        'b.context as context, u.username as username,'
        'u.id as author_id'
        ' FROM blog b JOIN user_blog u_b on b.id = u_b.blog_id'
        ' JOIN user u ON u.id = u_b.user_id '
        ' WHERE b.id = ?',
        (blog['ori_blog_id'], )
    ).fetchone()

    blog.update(ori_blog)
    blog['fork_id'] = user_id
    if check_author and blog['author_id'] != g.user['id']:
        abort(403)
    return blog


@bp.route('/<int:blog_id>/', methods=('GET', 'POST'))
@login_required
def create(blog_id):
    if request.method == 'POST':
        context = request.form['body']
        error = None

        if not context:
            context = fork_comment_default

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            ori_blog = cur.execute(
                'SELECT ori_blog_id, context '
                ' FROM blog b'
                ' WHERE b.id = ?',
                (blog_id,)
            ).fetchone()

            context = r'//@' + g.user['username'] + ':' + context
            if fork_comment_maxlength != -1:
                while len(context) > fork_comment_maxlength:
                    last_user_comment = context.rfind(r'//@')
                    # at least one user comment should be reverse
                    if last_user_comment <= 0:
                        break
                    context = context[:last_user_comment]

            if ori_blog['ori_blog_id'] != -1:
                blog_id = ori_blog['ori_blog_id']
                context = context + ori_blog['context']
            cur.execute(
                'INSERT INTO blog(ori_blog_id, context)'
                ' VALUES (?, ?)',
                (blog_id, context)
            )
            new_id = cur.lastrowid
            cur.execute(
                'INSERT INTO user_blog(user_id, blog_id)'
                'VALUES (?, ?)',
                (g.user['id'], new_id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('fork/create.html')


@bp.route('/<int:blog_id>/delete')
@login_required
def delete(blog_id, dated):
    db = get_db()
    db.execute('DELETE FROM blog WHERE blog_id = ? and user_id = ? and dated = ?',
               (blog_id, g.user['id'], dated))
    db.commit()
    g.fork.remove(blog_id)
    return redirect(url_for('blog.index'))


@bp.route('/<int:user_id>/<int:blog_id>/')
@login_required
def show_fork(user_id, blog_id):
    user = get_user(user_id)
    blog = get_forward(user_id=user_id, blog_id=blog_id, check_author=False)
    comments = get_comments_on_blog(blog_id)
    return render_template('fork/showFork.html', user=user, blog=blog, comments=comments)


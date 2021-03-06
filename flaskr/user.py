from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash


from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/all')
def users_index():
    db = get_db()
    users = db.execute(
        'SELECT username, id, dated'
        ' FROM user'
        ' ORDER BY dated DESC'
    ).fetchall()
    return render_template('user/index.html', users=users)


def get_user(user_id):
    db = get_db()
    user = db.execute(
        'SELECT username, id, dated, birthday, email, gender, telephone, introduction'
        ' FROM user'
        ' WHERE id=?',
        (user_id, )
    ).fetchone()
    if user is None:
        abort(404, "User id {0} doesn't exist.".format(user_id))
    return user


def get_user_and_blogs(id, check_login=True):
    db = get_db()
    user = db.execute(
        'SELECT username, id, dated, birthday, email, gender, telephone, introduction'
        ' FROM user'
        ' WHERE id=?',
        (id, )
    ).fetchone()
    if user is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_login:
        if g.user is None:
            return redirect(url_for('auth.login'))

    blogs = db.execute(
        'SELECT b.id, b.dated as dated, context, ori_blog_id,'
        'u.id as author_id, username'
        ' FROM blog b JOIN user_blog u_b ON b.id = u_b.blog_id JOIN user u ON u_b.user_id=u.id'
        ' WHERE u.id = ? and b.ori_blog_id == -1',
        (id,)
    ).fetchall()

    is_follower = False
    is_leader = False
    if not check_login and g.user is None:
        is_follower = False
        is_leader = False
    else:
        follower = db.execute(
            'SELECT follower_id'
            ' FROM follower'
            ' WHERE follower_id = ? and leader_id = ?',
            (g.user['id'], id)
        ).fetchone()

        leader = db.execute(
            'SELECT follower_id'
            ' FROM follower'
            ' WHERE follower_id = ? and leader_id = ?',
            (id, g.user['id'])
        ).fetchone()

        if follower is not None:
            is_follower = True
        if leader is not None:
            is_leader = True

    return user, blogs, is_follower, is_leader


def get_user_and_forks(id, check_login=True):
    db = get_db()
    user = db.execute(
        'SELECT username, id, dated, birthday, email, gender, telephone, introduction'
        ' FROM user'
        ' WHERE id=?',
        (id, )
    ).fetchone()
    if user is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_login:
        if g.user is None:
            return redirect(url_for('auth.login'))

    blog = db.execute(
        'SELECT b.id as id, b.dated as fork_time, '
        'b.context as fork_comment, u.username as fork_name,'
        'u.id as fork_id, b.ori_blog_id as ori_blog_id'
        ' FROM blog b JOIN user_blog u_b on b.id = u_b.blog_id'
        ' JOIN user u ON u.id = u_b.user_id '
        'WHERE u.id = ? and (b.ori_blog_id < -1 or b.ori_blog_id > 0)',
        (id, )
    ).fetchall()

    ori_blogs = []
    for i in blog:
        ori_blog = db.execute(
            'SELECT b.id as ori_id, b.dated as dated, '
            'b.context as context, u.username as username,'
            'u.id as author_id'
            ' FROM blog b JOIN user_blog u_b on b.id = u_b.blog_id'
            ' JOIN user u ON u.id = u_b.user_id '
            ' WHERE b.id = ?',
            (i['ori_blog_id'], )
        ).fetchone()
        ori_blogs.append(ori_blog)

    for i in range(len(blog)):
        blog[i].update(ori_blogs[i])
        blog[i]['fork_id'] = id

    delete_blogs = db.execute(
        'SELECT b.id, b.dated as fork_time, b.context as fork_comment,'
        ' b.ori_blog_id as ori_blog_id, u.id as fork_id, u.username as fork_username'
        ' FROM user u JOIN user_blog u_b on u.id = u_b.user_id JOIN blog b on u_b.blog_id = b.id'
        ' WHERE b.ori_blog_id == 0 and u.id = ?',
        (id, )
    ).fetchall()

    blog = blog + delete_blogs

    is_follower = False
    is_leader = False
    if not check_login and g.user is None:
        is_follower = False
        is_leader = False
    else:
        follower = db.execute(
            'SELECT follower_id'
            ' FROM follower'
            ' WHERE follower_id = ? and leader_id = ?',
            (g.user['id'], id)
        ).fetchone()

        leader = db.execute(
            'SELECT follower_id'
            ' FROM follower'
            ' WHERE follower_id = ? and leader_id = ?',
            (id, g.user['id'])
        ).fetchone()

        if follower is not None:
            is_follower = True
        if leader is not None:
            is_leader = True

    return user, blog, is_follower, is_leader


def get_user_and_followers(id, check_login=True):
    db = get_db()
    user = db.execute(
        'SELECT username, id, dated, birthday, email, gender, telephone, introduction'
        ' FROM user'
        ' WHERE id=?',
        (id, )
    ).fetchone()

    if user is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_login:
        if g.user is None:
            return redirect(url_for('auth.login'))

    follower = db.execute(
        'SELECT f.dated as follow_time, u.dated as dated, u.id as id, u.username as username'
        ' FROM follower f join user u'
        ' Where f.follower_id = u.id and f.leader_id = ?',
        (id,)
    ).fetchall()

    return user, follower


def get_user_and_leaders(id, check_login=True):
    db = get_db()
    user = db.execute(
        'SELECT username, id, dated, birthday, email, gender, telephone, introduction'
        ' FROM user'
        ' WHERE id=?',
        (id, )
    ).fetchone()

    if user is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_login:
        if g.user is None:
            return redirect(url_for('auth.login'))

    leader = db.execute(
        'SELECT f.dated as follow_time, u.dated as dated, u.id as id, u.username as username'
        ' FROM follower f join user u'
        ' Where f.leader_id = u.id and f.follower_id = ?',
        (id,)
    ).fetchall()

    return user, leader


def sort_by_creat_time(x):
    try:
        res = x['fork_time']
    except KeyError:
        res = x['dated']

    return res


@bp.route('/<int:user_id>/detail')
@login_required
def show_user(user_id):
    user, blogs, is_follower, is_leader = get_user_and_blogs(user_id, check_login=False)
    _, forks, _, _,  = get_user_and_forks(user_id, check_login=False)
    blogs = blogs + forks
    blogs = sorted(blogs, key=sort_by_creat_time, reverse=True)

    db = get_db()

    communities_id = db.execute(
        'SELECT community_id as id'
        ' FROM member'
        ' WHERE user_id = ?'
        ' ORDER by dated',
        (user_id, )
    ).fetchall()
    communities = []
    for i in communities_id:
        community = db.execute(
            'SELECT theme, id, description, dated, key_word'
            ' FROM community'
            ' WHERE id = ?'
            ' ORDER by dated',
            (i['id'], )
        ).fetchone()
        communities.append(community)

    communities = communities[:3]
    return render_template('user/showUser.html', user=user, blogs=blogs,
                           is_follower=is_follower, is_leader=is_leader,
                           communities=communities)


@bp.route('/<int:user_id>/communities')
@login_required
def show_community(user_id):
    db = get_db()

    user = db.execute(
        'SELECT username, id, dated, birthday, email, gender, telephone, introduction'
        ' FROM user'
        ' WHERE id=?',
        (user_id,)
    ).fetchone()

    communities = db.execute(
        'SELECT theme, description, key_word, id, dated'
        ' FROM community'
        ' WHERE user_id = ?'
        ' ORDER by dated',
        (user_id, )
    ).fetchall()
    return render_template('user/showCommunity.html',
                           communities=communities, username=user['username'])


@bp.route('/<int:user_id>/follow/<int:leader_id>')
@login_required
def follow_user(user_id, leader_id):
    db = get_db()

    db.execute(
        'INSERT INTO follower (follower_id, leader_id)'
        ' VALUES (?, ?)',
        (user_id, leader_id))
    db.commit()
    return redirect(url_for('user.show_user', user_id=leader_id))


@bp.route('/<int:user_id>/unfollow/<int:leader_id>')
@login_required
def unfollow_user(user_id, leader_id):
    db = get_db()

    db.execute(
        'DELETE FROM follower WHERE follower_id=? and leader_id=?',
        (user_id, leader_id))
    db.commit()
    g.leader.remove(leader_id)
    return redirect(url_for('user.show_user', user_id=leader_id))


@bp.route('/<int:user_id>/follower_list')
@login_required
def show_followers(user_id):
    user, followers = get_user_and_followers(user_id, check_login=False)
    return render_template('user/showFollowers.html', user=user, followers=followers)


@bp.route('/<int:user_id>/leader_list')
@login_required
def show_leaders(user_id):
    user, leaders = get_user_and_leaders(user_id, check_login=False)
    return render_template('user/showLeaders.html', user=user, leaders=leaders)


@bp.route('/search/', methods=('GET', 'POST'))
@login_required
def search():
    if request.method == 'POST':
        name = request.form['title']

        db = get_db()
        name = '%'+name+'%'
        users = db.execute(
            'SELECT id, dated, username'
            ' FROM user'
            ' Where user.username like ?',
            (name,)
        ).fetchall()
        name = name[1:-1]
        
        return render_template('user/show_search_res.html', users=users, name=name)

    return render_template('user/search.html')


@bp.route('/<int:user_id>/update', methods=('GET', 'POST'))
@login_required
def update(user_id):
    user = get_user(user_id)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        birthday = request.form['birthday']
        email = request.form['email']
        gender = request.form['gender']
        telephone = request.form['telephone']
        introduction = request.form['introduction']
        error = None

        if not username:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:

            db = get_db()
            db.execute(
                'UPDATE user SET username = ?, password = ?,'
                'birthday = ?, email = ?, gender = ?, telephone = ?,'
                'introduction = ?'
                ' WHERE id = ?',
                (username, generate_password_hash(password),
                 birthday, email, gender, telephone, introduction, user_id)
            )
            db.commit()
            return redirect(url_for('user.show_user', user_id=user_id))

    return render_template('user/update.html', user=user)

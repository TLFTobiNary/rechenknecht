import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, abort, url_for, make_response
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from os import mkdir

bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('You need to be logged in to do that.', 'primary')
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif g.user['privileges'] > 0:
            return view(**kwargs)
        else:
            flash('You need an admin to do that', 'danger')
            return abort(403)
    return wrapped_view

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
                "select * from users where id = ?", (user_id,)
                ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == "POST":
        username = request.form['user']
        password = request.form['pass']
        db = get_db()
        error = None
        user = db.execute(
                "select password, id from users where username = ?", (username,)
                ).fetchone()
        if user is None:
            error = "Login failed."
        elif not check_password_hash(user['password'], password):
            error = "Login failed."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for('index'))

        flash(error, 'danger')
        return render_template('auth/login.html', error=True, user=username)

    return render_template("auth/login.html")

@bp.route('/reset/<string:username>', methods=("POST",))
def reset(username):
    db = get_db()
    data = db.execute("select password, id from users where username = ?", (username,)).fetchone()
    if (check_password_hash(data["password"], request.form["oldpass"])): 
        db.execute("update users set password = ? where username = ?", (generate_password_hash(request.form["newpass"]), username))
        db.commit()
        flash("New password set.", 'success')
        return redirect(url_for("index"))
    else:
        flash("That didn't work out. Are you sure you didn't mistype?", 'danger')
        return redirect(url_for('index'))

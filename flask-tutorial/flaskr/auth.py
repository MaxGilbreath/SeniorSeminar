import functools
import psutil

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
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/para', methods=('GET', 'POST'))
def parameters():
    if request.method == 'POST':
        c = request.form['cpu']
        r = request.form['ram']
        d = request.form['disk']
        t = request.form['time']
        kw = request.form['kw']
        if request.form['submit'] == 'Set':

            procs = []  # adapted from https://stackoverflow.com/questions/18460147/how-to-kill-specific-process-using-cpu-over-given-time-in-python-on-linux
            for process in psutil.process_iter():
                procs.append(process)

                for proc in procs:
                    for _ in range(60):
                        # check cpu percentage
                        if proc.get_cpu_percent(t) < c or not proc.is_running():
                            break
#                        elif proc.get_ram_percent(t) < c or not proc.is_running():
#                            break
#                        elif proc.get_disk_percent(t) < c or not proc.is_running():
#                            break
#                        elif do warnings
#                            break
                    else:
                        proc.terminate()

    return render_template('auth/para.html')



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
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


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

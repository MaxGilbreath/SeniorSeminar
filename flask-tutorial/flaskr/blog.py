import os
import psutil
import traceback
from psutil._common import bytes2human
import pandas as pd
import re

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)
pd.options.display.max_rows = 999


@bp.route('/')
def index():

    processes = list()
    for proc in psutil.process_iter():
        p = proc.as_dict(attrs=['pid', 'name', 'cpu_percent'])
        #get vms usage as ram
        p['ram_percent'] = proc.memory_info().vms / (1024 * 1024)

        processes.append(p)
    #total available ram
    mem = psutil.virtual_memory().available
    e = str(mem)
    t = ("Ram Available: " + e[0:2] + "GB")

    #total used disk
    o = str(psutil.disk_usage(
        '.').percent)  # adapted from https://www.programcreek.com/python/example/53878/psutil.disk_usage
    a = ("|| Disk Usage: " + o + "%")

    #total used cpu
    u = str(psutil.cpu_percent())
    v = ("|| CPU Usage: " + u + "%")

    return render_template('blog/index.html', posts=processes, vm=t, disk=a, cpu=v)


@bp.route('/', methods=('GET', 'POST'))
def killp():  # Adapted from https://gist.github.com/ayushxx7/ad0f0ba853e7b95c1d898f127c7c1e8f
    if request.method == 'POST':
        kp = request.form['pname']
        if request.form['submit_button'] == 'Kill Process':
            try:
                for proc in psutil.process_iter():
                    try:
                        if kp == proc.name():
                            proc.terminate()
                    except Exception:
                        print(f"{traceback.format_exc()}")
            except Exception:
                print(f"{traceback.format_exc()}")


#        elif request.form['submit_button'] == 'Do Something Else':
#            pass  # do something else
#        else:
#            pass  # unknown
#    elif request.method == 'GET':
#        return render_template('contact.html', form=form)


# def get_processes():
# Gives a list of the processes as a dictionary containing pid and name of a process
#    processes = list()
#    for proc in psutil.process_iter():
#       p = proc.as_dict(attrs=['pid', 'name'])
#       processes.append(p)
#  return processes


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

from . import printer
from ..models import Print, db_lock
from flask import request, url_for, redirect, render_template, jsonify, flash
from flask_login import login_required, current_user
from ..home.views import add_login_form
from .. import db
from ..main import task_queue, conn
from . import upload_file
import json
from datetime import datetime
from rq.job import Job


@printer.route('/printer/file', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash({
               'type':'error',
               'title':'No file part!',
               'text':'',
               'icon':''
        })
        return redirect(url_for('home.index'))
    file = request.files['file']
    if file.filename == '':
        flash({
               'type':'error', 
               'title':'No selected file!',
               'text':'',
               'icon':''
        })
        return redirect(url_for('home.index'))
    
    file_path = upload_file(file)
    if file_path:
        return jsonify(path=file_path, elementID='model', original_file=file.filename), '202'
    else: 
        return '404'


@printer.route('/printer/result', methods=['GET', 'POST'])
@login_required
def result():
    with db_lock:
        rows = Print.query.filter_by(user_id=current_user.id, complete=True).all()
    if rows:
        for row in rows:
            row.user_checked =  True
        with db_lock:
            db.session.commit()
        return render_template('home/result.html', rows=rows)
    else:
        return render_template('home/result.html')
    


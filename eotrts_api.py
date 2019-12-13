import os

import MySQLdb
import jiwer

from flask import Flask, flash, request, redirect, url_for
from flask_api import status, exceptions
from werkzeug.utils import secure_filename
from file_processing.receive_file import check_exist
from flask import send_from_directory
from database import DBMain
from cloud import upload_cloud
from mail_transfer import MailTransfer

app = Flask(__name__)
UPLOAD_FOLDER = r'C:\Users\lin\Desktop\Django_Apache\EOTRTS_Flask\record//'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = DBMain.DBMain()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/eotrts/student/<student_id>/", methods=['GET', 'POST'])
def student_inform(student_id):
    if request.method == "GET":
        stu_data = db.get_student_inform(student_id)
        if stu_data == 'no account':
            return '', status.HTTP_404_NOT_FOUND
        else:
            return stu_data
    elif request.method == "POST":
        update_course_date = request.json
        db.update_progress(update_course_date)
        return "update completed"


@app.route("/eotrts/english_essential_word/word/<unit>/", methods=['GET'])
def get_unit_words(unit):
    unit_words = db.get_word(unit)
    if unit_words == '':
        return '', status.HTTP_404_NOT_FOUND
    else:
        return unit_words


@app.route("/eotrts/english_essential_word/quiz/<unit>/", methods=['GET', 'POST'])
def get_unit_quizzes(unit):
    if request.method == 'GET':
        try:
            unit_quizzes = db.get_quiz(unit)
        except MySQLdb.OperationalError:
            db.operation_error()
            unit_quizzes = db.get_quiz(unit)
        if unit_quizzes == '':
            return '', status.HTTP_404_NOT_FOUND
        else:
            return unit_quizzes
    elif request.method == 'POST':
        stu_data = request.json
        sid, unit = db.record_quiz_answer(stu_data)
        if MailTransfer.send_mail(sid, unit):
            return "success"
        else:
            return stu_data, status.HTTP_403_FORBIDDEN


@app.route("/eotrts/word_error_rate/", methods=['GET'])
def word_error_rate():
    truth = request.form.get('truth')
    say = request.form.get('say')
    correct_rate = (1-jiwer.wer(truth, say)) * 100
    correct_rate = int(correct_rate)
    word_correct_rate = {'wer': correct_rate}

    return word_correct_rate


@app.route('/upload/<student_id>/', methods=['GET', 'POST'])
def upload_file(student_id):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        check_exist(student_id)
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:
                check_exist(student_id)
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'] + student_id, filename))
                return "uploaded"
            except ConnectionError:
                app.logger.info("connection error")
            finally:
                filename = secure_filename(file.filename)
                file_path = app.config['UPLOAD_FOLDER'] + student_id + '//' + filename
                upload_cloud.upload_and_record(db, student_id, file_path)
            # redirect(url_for('uploaded_file',
            #                        student_id=student_id,
            #                        filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/uploads/<student_id>/<filename>/')
def uploaded_file(student_id, filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'] + '/' + student_id,
                               filename)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)

import time
import os
import subprocess
import urllib.request
from flask_cors import CORS

from flask_mysqldb import MySQL
import PyPDF2 as pypdf
from flask_mail import Mail, Message
import threading

from flask import Flask, request, redirect, jsonify, copy_current_request_context
from werkzeug.utils import secure_filename

welcome_message = "Welcome to Online Printing. You have successfully registered with us.\nThank you..."

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ssmmiitt007@gmail.com'
app.config['MAIL_PASSWORD'] = 'SP@88665'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root1234'
app.config['MYSQL_DB'] = "print"
mysql = MySQL(app)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}


def A4_BC(num: int):
    if 1 <= num <= 3:
        cost = 3
        return cost
    if 3 <= num < 30:
        cost = 3 + (num - 3) * 0.3
        return cost
    if 30 <= num < 100:
        cost = (29 * 0.3) + (num - 29) * 0.2
        return cost
    if num >= 100:
        cost = (99 * 0.2) + (num - 99) * 0.1
        return cost


def A3_BC(num: int):
    if 1 <= num <= 3:
        cost = 3
        return cost
    if 3 < num < 30:
        cost = 4 + (num - 3) * 0.6
        return cost
    if 30 <= num < 100:
        cost = (29 * 0.6) + (num - 29) * 0.4
        return cost
    if num >= 100:
        cost = (99 * 0.4) + (num - 99) * 0.2
        return cost


def A4_C(num: int):
    if 1 <= num <= 3:
        cost = 2
        return cost
    if 3 <= num < 30:
        cost = 2 + (num - 3) * 0.8
        return cost
    if 30 <= num < 100:
        cost = (29 * 0.6) + (num - 29) * 0.6
        return cost
    if num >= 100:
        cost = (99 * 0.4) + (num - 99) * 0.4
        return cost


def A3_C(num: int):
    if num == 1:
        cost = 3
        return cost
    if 2 <= num < 30:
        cost = 3 + (num - 1) * 0.3
        return cost
    if 30 <= num < 100:
        cost = (29 * 1.6) + (num - 29) * 1.2
        return cost
    if num >= 100:
        cost = (99 * 1.2) + (num - 99) * 0.8
        return cost


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/register', methods=['POST'])
def register():
    @copy_current_request_context
    def send_email(receiver):
        msg = Message('Welcome to Print', sender=app.config['MAIL_USERNAME'], recipients=[receiver])
        print(msg)
        msg.body = welcome_message
        mail.send(msg)

    start = time.perf_counter()
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            json_data = request.json
            email = json_data.get('email', 0)
            first_name = json_data.get('first_name', 0)
            last_name = json_data.get('last_name', 0)
            password = json_data.get('password', 0)
            mobile = int(json_data.get('mobile', 0))
            print(email, first_name, last_name, password, mobile)
            if email and first_name and last_name and password and mobile:
                qry = "insert into user (email, password, first_name, last_name, mobile) values (%s,%s,%s,%s,%s)"
                values = (email, password, first_name, last_name, mobile)
                cur = mysql.connection.cursor()
                cur.execute(qry, values)
                mysql.connection.commit()
                # t1 = Process(target=send_email, args=(email,))
                # t1.start()
                # # t1.join()
                # send_email(email)
                thread = threading.Thread(target=send_email, args=(email,))
                thread.start()
                return {"Success": "Inserted Successfully"}
            else:
                print("Seconds", time.perf_counter() - start)
                return "Values are missing or not correct"
        else:
            return 'Content-Type not supported!'

    return "Server is Up and running"


@app.route('/multiple-files-upload', methods=['POST'])
def upload_file():
    print("In Upload API")
    # check if the post request has the file part
    size, typ = request.form['docFormat'].split('_')
    if 'files[]' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp

    files = request.files.getlist('files[]')

    errors = {}
    success = False

    num_dict = {'numbers': []}
    total_pages = 0
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(file.mimetype)

            if file.mimetype == "application/pdf":
                npath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(npath)
                with open(npath, 'rb') as fpath:
                    read_pdf = pypdf.PdfFileReader(fpath)
                    num_pages = read_pdf.getNumPages()
                    num_dict['numbers'].append({"filename": filename, 'pages': num_pages})
                    print("NUM DICT +++", num_dict)
                    total_pages += num_pages

            if file.mimetype == "image/jpeg" or file.mimetype == "image/png":
                if 'Total Images' in num_dict.keys():
                    num_dict['Total Images'] += 1
                else:
                    num_dict['Total Images'] = 1
                total_pages += 1

            if filename.rsplit(".")[1] == "doc" or filename.rsplit(".")[1] == "docx":
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                source = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                destination = app.config['UPLOAD_FOLDER']
                output = subprocess.run(
                    ["libreoffice", '--headless', '--convert-to', 'pdf', source, '--outdir', destination])
                print(output)
                new_dest = os.path.splitext(destination + f'/{filename}')[0] + ".pdf"
                with open(new_dest, 'rb') as fpath:
                    read_pdf = pypdf.PdfFileReader(fpath)
                    num_pages = read_pdf.getNumPages()
                    num_dict['numbers'].append({"filename": filename, 'pages': num_pages})
                    print(num_pages)
                    total_pages += num_pages
                print("On Going")
            success = True
        else:
            errors[file.filename] = 'File type is not allowed'
    num_dict['Total Pages'] = total_pages
    if size == "A4" and typ.lower() == 'color':
        num_dict['Total cost $'] = A4_C(total_pages)
    if size == "A4" and typ.lower() == 'bw':
        num_dict['Total cost $'] = A4_BC(total_pages)
    if size == "A3" and typ.lower() == 'color':
        num_dict['Total cost $'] = A3_C(total_pages)
    if size == "A3" and typ.lower() == 'bw':
        num_dict['Total cost $'] = A3_BC(total_pages)

    if success and errors:
        errors['message'] = 'File(s) successfully uploaded'
        resp = jsonify({"errors": errors, "number": num_dict})
        resp.status_code = 500
        return resp
    if success:
        resp = jsonify({'message': 'Files successfully uploaded', "numbers": num_dict})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp


job_msg = "Your job as an email posted"


@app.route('/uploads', methods=["POST"])
def attach_mail():
    files_details = []

    @copy_current_request_context
    def send_with_attachment(receiver, files):
        msg = Message(job_msg, sender=app.config['MAIL_USERNAME'], recipients=[receiver])
        print(msg)
        msg.body = "Your files"
        for file in files:
            msg.attach(file[0].filename, file[1],
                       open(os.path.join(app.config['UPLOAD_FOLDER'], file[0].filename), 'rb').read())
        mail.send(msg)

    for files in request.files.getlist('files[]'):
        files_details.append([files, files.mimetype])
    print(files_details)
    threading.Thread(target=send_with_attachment, args=('ssssmmmmiiiitttt@gmail.com', files_details)).start()
    return jsonify({"message":"OK"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)

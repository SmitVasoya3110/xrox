import time
import os
import subprocess
import json
import socket
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
import pymysql
import datetime
# from flask_jwt import current_identity
from flask_cors import CORS
import magic
from flask_mysqldb import MySQL
import PyPDF2 as pypdf
from flask_mail import Mail, Message
import threading

from flask import Flask, request, redirect, jsonify, copy_current_request_context
from werkzeug.utils import secure_filename

welcome_message = "Welcome to Online Printing. You have successfully registered with us.\nThank you..."
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
print(ip_address)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smit-->p-->this__is~secret886651234'
jwt = JWTManager(app)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ssssmmmmiiiitttt@gmail.com'
app.config['MAIL_PASSWORD'] = 'mqlgthtejpwtrocw'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['ORDER_MAIL'] = "ssmmiitt007@gmail.com"
mail = Mail(app)

app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_PASSWORD'] = 'print1234'
app.config['MYSQL_DB'] = "print"
mysql = MySQL(app)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 24

MIME = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'application/vnd.oasis.opendocument.text-master']

@app.errorhandler(413)
def too_large(e):
    return {"message":"File/s is/are too large. limit is 24 MB","limit":"24 MB"}, 413

@app.errorhandler(500)
def internal_error(e):
    return {"error" : "There is Internal Server Error"}

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


@app.route('/CustomerLogin', methods=['POST'])
def CustomerLogin():
    json_data = request.json
    email = json_data.get('Email_Id', '')
    password = json_data.get('Password', '')
    if not email or not password:
        return jsonify({"message": "Credential Needed"})
    try:
        cur = mysql.connection.cursor()
        # cur = con.cursor(pymysql.cursors.DictCursor)
        sql = """SELECT *
                 FROM `Customer_Master`
                 where Email_Id='""" + email + """' and Password='""" + password + """' and status='1'
              """
        # data = (Email_Id, password)
        cur.execute(sql)
        rows = cur.fetchone()
        cur.close()
        print(rows)

        if not rows:
            return jsonify({"message": "Enter Valid Email_Id or Password"}), 401

        # mysql.connection.close()
        if (len(rows) > 0):
            dic1 = {}

            dic2 = {}
            dic3 = {}
            expires = datetime.timedelta(hours=2)
            dic1["access_token"] = create_access_token(identity=rows[3], expires_delta=expires)
            # dic1["refresh_token"] = create_refresh_token(identity=i[3])

            dic2["role"] = "Customer"
            dic2["uuid"] = rows[0]

            dic3["displayName"] = rows[1]
            dic3["email"] = rows[3]
            dic3["photoURL"] = ""

            dic2["data"] = dic3

            dic1["user"] = dic2

            # res = jsonify(dic1)
            # res.status_code = 200
            return dic1

            # return res


    except Exception as e:
        print(e)
        return ({"error": "There was an error"})

def check_email(email):
    qry = "select Email_Id from Customer_Master where Email_Id = %s"
    # cur = mysql2.connection.cursor()
    cur = mysql.connection.cursor()
    cur.execute(qry, (email,))
    result = cur.fetchone()
    cur.close()
    if result:
        return 1
    else:
        return 0

@app.route("/Customer", methods=["POST"])
def register_user():  # add new Customer -- MYSQL table : Customer_Master
    try:
        @copy_current_request_context
        def send_email(receiver):
            msg = Message('Welcome to Print', sender=app.config['MAIL_USERNAME'], recipients=[receiver])
            print(msg)
            msg.body = welcome_message
            mail.send(msg)

        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        json_data = request.json
        email = json_data.get('Email_Id', '')
        first_name = json_data.get('FirstName', '')
        last_name = json_data.get('LastName', '')
        password = json_data.get('Password', '')
        mobile = json_data.get('Mobile', 0)
        if not email or not first_name or not last_name or not password:
            return {"message": "Fields are missing"}
        if check_email(email):
            return {"message": "Email is already in use"}
        status = 1
        sql = """INSERT INTO `Customer_Master` (`FirstName`, `LastName`, `Email_Id`, `Password`, `status`, `dateAdded`, `mobile`)
                 VALUES (%s,%s,%s,%s,%s,%s, %s);"""
        data = (first_name, last_name, email, password, status, dt_string, mobile)
        print("SQL QUERY AND DATA ", sql, data)
        cur = mysql.connection.cursor()
        cur.execute(sql, data)
        mysql.connection.commit()
        cur.close()
        threading.Thread(target=send_email, args=(email,)).start()

        resp = jsonify({'message': 'Customer Is Added Successfully'})
        resp.status_code = 200
        return resp
    except Exception as e:

        print(e)
        return {}, 400


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
@jwt_required()
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

            if file.mimetype == "image/jpeg" or file.mimetype == "image/png" or file.mimetype == "image/jpg":
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
                if 'Total_Images' in num_dict.keys():
                    num_dict['Total_Images'] += 1
                else:
                    num_dict['Total_Images'] = 1
                total_pages += 1

            if file.mimetype in MIME:
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
    num_dict['Total_Pages'] = total_pages
    if size == "A4" and typ.lower() == 'color':
        num_dict['Total_cost'] = round(A4_C(total_pages),2)
    if size == "A4" and typ.lower() == 'bw':
        num_dict['Total_cost'] = round(A4_BC(total_pages), 2)
    if size == "A3" and typ.lower() == 'color':
        num_dict['Total_cost'] = round(A3_C(total_pages), 2)
    if size == "A3" and typ.lower() == 'bw':
        num_dict['Total_cost'] = round(A3_BC(total_pages), 2)

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

@app.route('/place/order', methods=["POST"])
@jwt_required()
def place_order():
    try:
        json_data = request.json
        user_id = json_data.get('user_id', 0)
        size, typ = json_data.get('type', ' _ ').split('_')
        files = json_data.get('files', [])
        amount = json_data.get('amount')
        print(type(json.dumps(files)))
        print("++" * 20, type(user_id), size, typ, type(files), amount)
        qry = "insert into orders (user_id, size, type, files, amount) values (%s,%s,%s,%s,%s)"
        values = (user_id, size, typ, json.dumps(files), amount)
        cur = mysql.connection.cursor()
        cur.execute(qry, values)
        mysql.connection.commit()
        last_id = cur.lastrowid
        return jsonify({"message": "OK", "order_id": last_id, "amount": amount}), 200

    except Exception as e:
        return {"message": "Internal Server Error"}

#
# @app.route("/get", methods=["GET"])
# def fun():
#     qry = "select * from orders"
#     cur = mysql.connection.cursor()
#     cur.execute(qry)
#     res = list(cur.fetchall())
#     for items in res:
#         items = list(items)
#         items[4] = json.loads(items[4], object_hook=str)
#         print(items[4])
#
#     print(res)
#     return {"Res": res}

send = """
<h1>Your Order have been placed. following are the details
"""

@jwt_required()
@app.route('/confirm/order', methods=["POST"])
def confirm_payment():
    @copy_current_request_context
    def send_attachment(order_id: int, files: list, receiver: str):
        msg = Message('Order', sender=app.config['MAIL_USERNAME'], recipients=[app.config['ORDER_MAIL']])
        msg.body = f"Order has been received with <order_id:{order_id}> from <{receiver}>"
        print(files)
        for file in files:
            file = secure_filename(file)
            print(file)
            nme = os.path.join(app.config['UPLOAD_FOLDER'], file)
            print("Full Path.....=>",(os.path.join(app.config['UPLOAD_FOLDER'], file)))
            buf = open(nme, 'rb').read()
            print(magic.from_buffer(buf, mime=True))
            msg.attach(file, magic.from_buffer(buf, mime=True), buf)
        print(msg)
        mail.send(msg)
        msg = Message(job_msg, sender=app.config['MAIL_USERNAME'], recipients=[receiver])
        msg.body = send + f"\norder_id:{order_id} \n files:{files}"
        mail.send(msg)

    json_data = request.json
    order_id = json_data.get('order_id', 0)
    user_id = json_data.get('user_id', 0)
    files = json_data.get('fileNames', [])
    amount = json_data.get('Total_Cost', 0)
    email = json_data.get('email', '')
    size, typ = json_data.get('docFormat', ' _ ').split('_')
    typ = "color" if typ.lower() == "c" else "black & white"
    if order_id and files and amount and email:
        qry = "insert into payments (order_id, user_id,amount, is_successful) values (%s, %s, %s, %s)"
        cur = mysql.connection.cursor()
        cur.execute(qry, (order_id, user_id, amount, 1))
        mysql.connection.commit()
        threading.Thread(target=send_attachment, args=(order_id, files, email)).start()
        return {"message": "OK"}, 200


@jwt_required()
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
    return jsonify({"message": "OK"})


@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    @copy_current_request_context
    def send_email(receiver,url):
        msg = Message(sender=app.config['MAIL_USERNAME'], recipients=[receiver])
        print(msg)
        msg.body = str(url)
        mail.send(msg)

    # print("..",_doc_(request))

    # url = request.host_url + 'Reset'
    url="http://localhost:3000/Reset/"
    body = request.get_json()
    Email_Id = body.get('Email_Id')
    if not Email_Id:
        return {"message":"Email_Id is requred"},400

    sql = """
     SELECT * FROM `Customer_Master` where Email_Id = '"""+str(Email_Id)+"""' and status='1'
     """
    cur = mysql.connection.cursor()
    cur.execute(sql)
    result = cur.fetchone()
    cur.close()
    if not result:
        return {"message":"Invaild Email ID"},400
    print("result",result)
    print("headers",request.headers)

    expires = datetime.timedelta(hours=1)
    reset_token = create_access_token(str(result[3]), expires_delta=expires)
    # return 0
    url+=str(reset_token)
    print("url",url)
    thread = threading.Thread(target=send_email, args=(Email_Id,url)).start()
    # thread.start()
    return {"message": "email was send for reset password"}

@app.route('/reset-password', methods=['POST'])
def reset_password():
    body = request.json
    print("body",body)
    if body == None:
        return {"message":"Inavid JSON"},400
    reset_token = body.get('reset_token')
    Password = body.get('Password')
    if not reset_token or not Password:
        return {"message":"Plz Provide reset_token and password"},400

    user_id = decode_token(reset_token)['sub']
    print(user_id)
    print("user_id",user_id)
    if not user_id:
        return {"message":"Invaid Reset Tokan"},400

    if not check_email(user_id):
        return {"message":"Invalid User"}
    # sql = """
    #  SELECT * FROM `Customer_Master` where id = '"""+str(user_id)+"""' and status='1'
    #  """
    # cur = mysql.connection.cursor()
    # cur.execute(sql)
    # result = cur.fetchone()
    # cur.close()
    # if not result:
    #     return {"message":"Invaild User"},400


    sql="""
    update Customer_Master set Password='"""+str(Password)+"""'
    where Email_Id='"""+str(user_id)+"""' and status='1'
    """
    cur = mysql.connection.cursor()
    cur.execute(sql)
    mysql.connection.commit()
    # result = cursor.fetchone()
    cur.close()
    return {"message":"Password was reset"}


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000, debug=True, threaded=True)

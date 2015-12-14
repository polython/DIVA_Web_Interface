#!/home/bgiardie/envs/diva/bin/python
from datetime import datetime, date
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from requests import Request
import http.client
import xml.etree.ElementTree as ET
import time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
import re
import random

# from logging import DEBUG
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# app.logger.setLevel(DEBUG)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'diva.db')
app.config['SECRET_KEY'] = '\x8a&Ss.\\\x1eQ\xd35\xcf\x07\x87!\x1a\xebe\xf5\xb3\xfch\xc3\xb5\xad'
db = SQLAlchemy(app)

# old array for testing
# reqstatus = []

# initial data structure for testing before DB integration
'''def store_req(url):
    reqstatus.append(dict(
        url=url,
        reqnum=1,
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
'''


# class for new tape entries
class Tape0:

    numrequests = 0

    # class implementation for counting requests independent of DB primary key
    @staticmethod
    def _inc_req_num():
        Tape0.numrequests += 1
        num = Tape0.numrequests
        return num

    def scheme(self):
        if not self.barcode:
            return "No barcode found"
        elif len(self.barcode) > 8:
            return "Invalid barcode"
        else:
            return "{}".format(self.barcode)

    def __init__(self, barcode):
        self.barcode = barcode
        # self.reqnum = Tape._inc_req_num()

    def __str__(self):
        return self.scheme()


# function to check for active requests
def cur_request():
    currequest = Tape.query.all()
    if len(currequest) == 0:
        return "No Valid Requests!"
    try:
        inc = len(currequest) - 1
        tryrequest = currequest[inc].reqst
        code = get_session_code()
        if get_req_status(code, tryrequest) == -1:
            return "No Active Requests"
        elif get_req_status(code, tryrequest) < 100:
            return " {} is the active request".format(tryrequest)
        else:
            return "No Active Requests"
    except:
        return "Something went wrong with the query!"


def active_import_chk():
    sescode = get_session_code()
    reqs = Tape.query.all()
    if len(reqs) == 0:
        return "No previous requests found!"
    reqinc = len(reqs) - 1
    active = 0
    for rqst in range(0, 10, 1):
        if get_req_type(sescode, reqs[reqinc - rqst].reqst) == 4:
            if get_req_progress(sescode, reqs[reqinc - rqst].reqst) == 12:
                active += 1
        continue
    for rqst in range(0, 250, 1):
        if get_req_type(sescode, reqs[reqinc].reqst + rqst) != -1:
            if get_req_type(sescode, reqs[reqinc].reqst + rqst) == 4:
                if get_req_progress(sescode, reqs[reqinc].reqst + rqst) == 12:
                    active += 1
        continue
    if active != 0:
        return -1
    else:
        return 0


# function to get last request from DB
def get_last_request():
    lastreq = Tape.query.all()
    if len(lastreq) == 0:
        return "No previous requests found!"
    reqinc = len(lastreq) - 1
    request_ = lastreq[reqinc].reqst
    return request_


# function to parse DB query object from a request number
def get_db_entry(val):
    id_ = int(val)
    query = db.session.query(Tape).filter(Tape.reqst == id_)
    result = query.all()
    if len(result) != 0:
        if len(result) > 1:
            last = len(result) - 1
            return [result[last].reqst, result[last].barcode]
        else:
            return [result[0].reqst, result[0].barcode]
    else:
        return "No record for this request"


# function to parse DB query object for a tape
def get_tape_entry(tape):
    query = db.session.query(Tape).filter(Tape.barcode == tape)
    result = query.all()
    if len(result) != 0:
        if len(result) > 1:
            last = len(result) - 1
            return result[last].reqst
        else:
            return result[0].reqst
    else:
        return False


# call to API function to get request progress
def get_status(sescode, serreqid):
    serreqid = serreqid
    sescode = sescode
    if check_stat_comp(sescode, serreqid) == -1:
        flash('{} failed, please check request ID or Spectra panel'.format(serreqid))
        return redirect(url_for('status'))
    elif check_stat_comp(sescode, serreqid) == -2:
        flash('{} not a valid request ID'.format(serreqid))
        return redirect(url_for('status'))
    elif check_stat_comp(sescode, serreqid) < 100:
        flash('Request still in progress!')
        return redirect(url_for('status'))
    else:
        reqid = get_db_entry(serreqid)[0]
        barcode = get_db_entry(serreqid)[1]
        flash('Request number {} for tape {} completed'.format(reqid, barcode))
        # app.logger.debug('added request: ' + url)
        return redirect(url_for('status'))


# root site handler
@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    # POST request to submit tape restore; validate field; check for barcodes; submit API call; return job ID and status
    if request.method == "POST":
        if active_import_chk() != 0:
            flash('Import Request Already In Progress! Your Tapes Will Also Be Imported!')
            return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
        if str(request.form['tape']):
            if len(request.form['tape']) > 9:
                bcodes = (request.form['tape']).split(' ')
                sescode = get_session_code()
                tapereq = insert_tape(sescode)
                for bcode in bcodes:
                    newtape = bcode.upper()
                    tp = Tape0(newtape)
                    tpdb = Tape(barcode=tp.barcode, reqst=tapereq)
                    db.session.add(tpdb)
                    db.session.commit()
                time.sleep(5)
                while get_req_progress(sescode, tapereq) == 12:
                    continue
                else:
                    if get_req_progress(sescode, tapereq) == 3:
                        flash('Tapes {} restored, with request {}'.format(' '.join(bcodes), tapereq))
                        return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
                    else:
                        flash('Request has failed, please verify Spectra import completed!'.format(tapereq))
                        return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
               # return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
            else:
                newtape = request.form['tape']
                tp = Tape0(newtape)
                sescode = get_session_code()
                tapereq = insert_tape(sescode)
                tpdb = Tape(barcode=tp.barcode, reqst=tapereq)
                db.session.add(tpdb)
                db.session.commit()
                time.sleep(5)
                while get_req_progress(sescode, tapereq) == 12:
                    continue
                else:
                    if get_req_progress(sescode, tapereq) == 3:
                        flash('Tape {} restored, with request {}'.format(tp.barcode, tapereq))
                        return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
                    else:
                        flash('Request has failed, please verify Spectra import completed!'.format(tapereq))
                        return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
                # return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
        # create placeholder in DB if no barcodes are entered for restore
        else:
            sescode = get_session_code()
            tapereq = insert_tape(sescode)
            tpdb = Tape(barcode="D00000", reqst=tapereq)
            db.session.add(tpdb)
            db.session.commit()
            time.sleep(5)
            while get_req_progress(sescode, tapereq) == 12:
                continue
            else:
                if get_req_progress(sescode, tapereq) == 3:
                    flash('Request {} completed for inserted tapes.'.format(tapereq))
                    return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
                else:
                    flash('Request has failed, please verify Spectra import completed!'.format(tapereq))
                    return render_template('index.html', title1=get_last_request(), reqstat=cur_request())
    return render_template('index.html', title1=get_last_request(), reqstat=cur_request())


# request status page handler
@app.route('/status', methods=['GET', 'POST'])
def status():
    # check if POST; parse input for request number or barcode; call status function and return; reload page if GET
    if request.method == "POST":
        sescode = get_session_code()
        if re.match(r'D\d{5,7}', request.form['reqnumber'], re.I):
            bcode = 'D' + request.form['reqnumber'][1:]
            req = get_tape_entry(bcode)
            if req:
                return get_status(sescode, req)
            else:
                flash("Not a valid barcode!")
                return render_template('status.html')
        try:
            int(request.form['reqnumber'])
        except ValueError:
            flash("Please enter a valid 4 digit request ID or Barcode")
            return redirect(url_for('status'))
        if re.match(r'\d{4}', request.form['reqnumber']):
            serreqid = request.form['reqnumber']
            return get_status(sescode, serreqid)
        else:
            flash("Please enter a valid ID for the request")
    return render_template('status.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/sop')
def sop():
    return render_template('SOP.html')


# error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# API call to re-import a tape
def insert_tape(skey):

    sessionkey = str(skey)
    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\">\r\n" \
              "<env:Body>\r\n" \
              "<p:insertTape xmlns:p=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xs:sessionCode xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" + sessionkey +"</xs:sessionCode>\r\n    " \
              "<xs:require xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">0</xs:require>\r\n    " \
              "<xs:priorityLevel xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">50</xs:priorityLevel>\r\n    " \
              "<xs:acsId xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">0</xs:acsId>\r\n    " \
              "<xs:capId xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">0</xs:capId>\r\n    " \
              "</p:insertTape>\r\n" \
              "</env:Body>\r\n" \
              "</env:Envelope>"

    headers = {
        'accept': "application/xml",
        'content-type': "text/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/insertTape", payload, headers)

    res = conn.getresponse()
    data = res.read()

    root = ET.fromstring(data.decode('UTF8'))
    requestnumber = root[0][1].text

    return requestnumber


# API call to register client and return session code
def get_session_code():

    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<xsd:registerClient xmlns:xsd=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xsd:appName>Tape Test Application</xsd:appName>\r\n    " \
              "<xsd:locName>1</xsd:locName>\r\n    " \
              "<xsd:processId>1</xsd:processId>\r\n" \
              "</xsd:registerClient>"

    headers = {
        'content-type': "application/xml",
        'accept': "application/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/registerClient", payload, headers)

    res = conn.getresponse()
    data = res.read()

    # clientcode = xmltodict.parse(data.decode('UTF8'))

    root = ET.fromstring(data.decode('UTF8'))
    sessioncode = root[0].text

    return sessioncode


# model class for DB tape table
class Tape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String, nullable=False)
    reqst = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=date.today())

    # req_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)

    @staticmethod
    def find_tape(barcode):
        if not barcode:
            return "No barcode found"
        elif len(barcode) > 8:
            return "Invalid barcode"
        else:
            return Tape.query(Tape.barcode).all()

    def __repr__(self):
        return "Tape with barcode {} was restored on {}".format(self.barcode, self.date)


# model class for DB request table (not implemented)
'''class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reqnum = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=date.today())

    barcodes = db.relationship('Tape', backref='req', lazy='dynamic')

    @staticmethod
    def find_diva_req(req):
        if not req:
            return "Please provide a request number"
        else:
            return Request.query(Request.reqnum).all()

    def __repr__(self):
        return "Diva request number {}".format(self.reqnum)
'''


def initdb():
    db.create_all()
    print("Initialized the database")


def dropdb():
    db.drop_all()
    print("Dropped the database")


# API call to check request status (complete, failed, etc)
def get_req_status(skey, rid):

    sessionkey = str(skey)
    reqid = str(rid)

    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\">\r\n" \
              "<env:Body>\r\n<p:getRequestInfo xmlns:p=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xs:sessionCode xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + sessionkey + "</xs:sessionCode>\r\n    " \
              "<xs:requestNumber xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + reqid + "</xs:requestNumber>\r\n</p:getRequestInfo>\r\n" \
              "</env:Body>\r\n</env:Envelope>"

    headers = {
        'accept': "application/xml",
        'content-type': "text/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/getRequestInfo", payload, headers)

    res = conn.getresponse()
    data = res.read()

    root = ET.fromstring(data.decode('UTF8'))
    divareqstat = root[0][0].text

    if int(divareqstat) != 1000:
        return 3
    else:
        progress = root[0][1][4].text

    return int(progress)


# check if request is completed
def check_stat_comp(key, id_):
    if get_req_status(key, id_) == -1:
        print("Request failed, please verify a tape is inserted")
        return -1
    elif get_req_status(key, id_) == 3:
        print("No such request")
        return -2
    elif get_req_status(key, id_) != 100:
        return -3
    else:
        print("Request complete, tape has been re-imported")
        return 100


# API call to get current request progress
def get_req_progress(skey, rid):

    sessionkey = str(skey)
    reqid = str(rid)

    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\">\r\n" \
              "<env:Body>\r\n<p:getRequestInfo xmlns:p=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xs:sessionCode xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + sessionkey + "</xs:sessionCode>\r\n    " \
              "<xs:requestNumber xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + reqid + "</xs:requestNumber>\r\n</p:getRequestInfo>\r\n" \
              "</env:Body>\r\n</env:Envelope>"

    headers = {
        'accept': "application/xml",
        'content-type': "text/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/getRequestInfo", payload, headers)

    res = conn.getresponse()
    data = res.read()

    root = ET.fromstring(data.decode('UTF8'))
    divareqstat = root[0][0].text

    if int(divareqstat) != 1000:
        return -1
    else:
        progress = root[0][1][7].text

    return int(progress)


def get_req_type(skey, rid):

    sessionkey = str(skey)
    reqid = str(rid)

    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\">\r\n" \
              "<env:Body>\r\n<p:getRequestInfo xmlns:p=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xs:sessionCode xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + sessionkey + "</xs:sessionCode>\r\n    " \
              "<xs:requestNumber xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + reqid + "</xs:requestNumber>\r\n</p:getRequestInfo>\r\n" \
              "</env:Body>\r\n</env:Envelope>"

    headers = {
        'accept': "application/xml",
        'content-type': "text/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/getRequestInfo", payload, headers)

    res = conn.getresponse()
    data = res.read()

    root = ET.fromstring(data.decode('UTF8'))
    divareqstat = root[0][0].text

    if int(divareqstat) != 1000:
        return -1
    else:
        r_type = root[0][1][8].text

    return int(r_type)

if __name__ == '__main__':
    app.debug = True
    app.run(threaded=True)

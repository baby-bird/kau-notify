#-*- coding: utf-8 -*-
from flask import Flask, request,session, redirect, url_for, abort, render_template, flash, send_from_directory
from models import *
import re
from app import app
from itsdangerous import URLSafeSerializer, BadData
from google.appengine.ext import ndb
from google.appengine.api import memcache
from config import *
import logging
import sendgrid
from sendgrid.helpers import mail
import requests, requests_toolbelt.adapters.appengine
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

BoardDict = {"General": "일반", \
             "Academic": "학사", \
             "Scholar": "장학/대출", \
             "Career": "취업", \
             "Event": "행사", \
             "Employ": "모집/채용", \
             "Dormitory": "생활관", \
             "AME": "항공우주 및 기계공학부", \
             "ETC": "항공전자정보공학부", \
             "AVS": "항공재료공학과", \
             "SOF": "소프트웨어학과", \
             "ATL": "항공교통물류학부", \
             "BUS": "경영학부", \
             "AEO": "항공운항학과"}

@app.route('/')
@app.route('/index')
def index():
    # ----Comment this Section when testing----
    qry= Counter.query()
    for c in qry.fetch(1):
        TotalSubs = c.counter
    # ----------------------------------------
    # s = URLSafeSerializer(app.secret_key, salt=Noti_Setting_Token)#<---------gitignore시 반드시 삭제할 것!
    # token = s.dumps('some_email')
    # url = "http://localhost:8080/notificationSettings/" + token
    # logging.info(url)
    # TotalSubs = len(Subs.query().fetch(keys_only=True)) #This takes too much datastore small ops
    # TotalSubs = memcache.get(key="TotalSubs")
    return render_template('index.html', total_subscribers=TotalSubs)

@app.route('/robots.txt')

@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/googlea2daa27b7e694cb6.html')
def google():
    return render_template('googlea2daa27b7e694cb6.html')

@app.route('/navere5d490ca72e940020a850a38580bc312.html')
def naver():
    return render_template('navere5d490ca72e940020a850a38580bc312.html')

@app.route('/developer')
def developer():
    return render_template('developer.html')

# @app.route('/notice_email')
# def notice_email():
#     return render_template('notice.html')

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

@app.route('/subscribe', methods=['POST', 'GET'])
def subscribe():
    requests_toolbelt.adapters.appengine.monkeypatch()
    VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": RECAPCHA_SECRET_KEY,
        "response": request.form.get('g-recaptcha-response'),
        "remoteip": request.environ.get('REMOTE_ADDR')
    }
    r = requests.get(VERIFY_URL, params=data)
    VERIFIED = r.json()["success"] if r.status_code == 200 else False
    if VERIFIED:
        if request.method == 'POST':
            ame = "항공우주 및 기계공학부"
            etc = "항공전자정보공학부"
            avs = "항공재료공학과"
            sof = "소프트웨어학과"
            atl = "항공교통물류학부"
            bus = "경영학부"
            aeo = "항공운항학과"

            deptset = {bus, sof, atl, ame, aeo, avs, etc}

            dept = request.form['dept']
            email = request.form['email']
            comment = request.form['comment']

            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
            if match != None:
                qry = Subs.query(Subs.email == email)
                for mail in qry.fetch(1):
                    if str(mail.email) == email:
                        return '''<script type="text/javascript">
                                alert('이미 구독 하셨습니다! ( ͡° ͜ʖ ͡°)');
                                window.location= "/";
                                </script>'''
                if BoardDict[dept] in deptset and not qry.fetch(1):
                    S = Subs()
                    S.email = email
                    S.comment = comment
                    S.subsboard= [
                        MainBoard(type = 'General'),
                        MainBoard(type = 'Academic'),
                    ]
                    S.deptboard = [
                        DeptBoard(
                            type = dept)
                    ]
                    S.put()

                    counter_qry = Counter.query()
                    for c in counter_qry.fetch(1):
                        c.counter += 1
                        c.put()
                    # memcache.incr("TotalSubs")
                    return '''<script type="text/javascript">
                            alert("등록 했습니다.\\n(매일 오후 9시에 만나요~~!!! 새 글이 없으면 말구요ㅎㅎ)");
                            window.location= "/";
                            </script>'''
                else:
                    return '''
                        <script type="text/javascript">
                        alert('잘못된 접근을 시도하고있습니다.');
                        window.location= "/";
                        </script>'''
            else:
                return '''
                <script type="text/javascript">
                alert('올바른 이메일을 입력하세요-_-');
                window.location= "/";
                </script>'''
    else:
        return '''
            <script type="text/javascript">
            alert('잘못된 접근을 시도하고있습니다.');
            window.location= "/";
            </script>'''

@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    s = URLSafeSerializer(app.secret_key, salt=Noti_Setting_Token)
    try:
        email = s.loads(token)
    # --------------------------
        logging.info(email)
    # --------------------------

    except BadData:
        # show an error
        return '''
        <script type="text/javascript">
        alert('잘못된 접근입니다.');
        window.location= "/";
        </script>'''

    # unsubscribe
    qry = Subs.query(Subs.email == email)
    if not qry.fetch(1):
        return '''
                <script type="text/javascript">
                alert('존재하지 않는 구독자 입니다.');
                window.location= "/";
                </script>'''
    user = qry
    if user:
        user.get().key.delete()  # DB에서 삭제

        U = Unsubs() #구독 취소자 행동패턴 파악 위해 따로 DB생성
        U.put()

        counter_qry = Counter.query()
        for c in counter_qry.fetch(1):
            c.counter -= 1
            c.put()
        return '''
                <script type="text/javascript">
                alert('구독이 취소되었습니다.');
                window.location= "/";
                </script>'''

# 게시판 선택
@app.route('/notificationSettings/<token>')
def notificatinoSettings(token):
    s = URLSafeSerializer(app.secret_key, salt=Noti_Setting_Token)
    try:
        email = s.loads(token)

    except BadData:
        # show an error
        return '''
            <script type="text/javascript">
            alert('잘못된 접근입니다.');
            window.location= "/";
            </script>'''

    qry = Subs.query(Subs.email == email)

    if not qry.fetch(1):
        return '''
                <script type="text/javascript">
                alert('구독이 취소된 사용자 입니다.');
                window.location= "/";
                </script>'''
    user = qry
    if user:
        for user in qry.fetch(1):
            subsboardlst=[]
            for i in user.subsboard:
                subsboardlst.append(BoardDict[i.type])
            deptboardlst = []
            for i in user.deptboard:
                deptboardlst.append(BoardDict[i.type])
            email=user.email
            url = "https://kau-notify.appspot.com/unsubscribe/" + token
        return render_template('notificationSettings.html', dept=deptboardlst, email=email, subsboard=subsboardlst, unsuburl=url, \
                                    token=token)

# 게시판 선택권 저장
@app.route('/notificationSettings/<token>/set', methods=['POST', 'GET'])
def set(token):
    if request.method == 'POST':
        s = URLSafeSerializer(app.secret_key, salt=Noti_Setting_Token)
        try:
            email = s.loads(token)

        except BadData:
            # show an error
            return '''
                <script type="text/javascript">
                alert('잘못된 접근입니다.');
                window.location= "/";
                </script>'''

        qry = Subs.query(Subs.email == email)
        if not qry.fetch(1):
            return '''
                    <script type="text/javascript">
                    alert('구독이 취소된 사용자 입니다.');
                    window.location= "/";
                    </script>'''

        else:
            selected_board = request.form.getlist("gen_board")
            selected_dept = request.form.getlist("dept_board")
            if not selected_board and not selected_dept:
                return '''
                        <script type="text/javascript">
                        alert('적어도 한개의 게시판을 선택하세요.');
                        </script>'''
            elif len(selected_dept)>2:
                return '''
                        <script type="text/javascript">
                        alert('학부 게시판은 2개까지 가능합니다.');
                        </script>'''
            else:
                for user in qry.fetch(1):
                    if str(user.email) == email:
                        user.subsboard=[]
                        for i in selected_board:
                            user.subsboard.append(MainBoard(type=i))
                        user.deptboard=[]
                        for i in selected_dept:
                            user.deptboard.append(DeptBoard(type=i))
                        user.put()
                    return '''
                            <script type="text/javascript">
                            alert('설정이 저장 되었습니다.');
                            window.location= "/";
                            </script>'''
    else:
        return '''
            <script type="text/javascript">
            alert('잘못된 접근을 시도하고있습니다.');
            window.location= "/";
            </script>'''


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return '앗! 이 주소엔 아무것도 없어요.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return '앗! 예기치 않은 문제가 발생했습니다. : {}'.format(e), 500

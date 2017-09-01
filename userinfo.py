# -*- coding: utf-8 -*-
from google.appengine.ext import ndb
# from google.appengine.api import memcache
from datetime import date
from datetime import datetime as dt
import requests, smtplib, re, os, sys
from bs4 import BeautifulSoup
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from app import app
import logging, requests_toolbelt.adapters.appengine, lxml
from app.models import Subs
from app.config import *
from google.appengine.api import mail
import pytz, time
import sendgrid
from sendgrid.helpers.mail import *
from google.appengine.api import urlfetch
from google.appengine import runtime

urlfetch.set_default_fetch_deadline(60)

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

home_url = "http://kau.ac.kr/page/kauspace"
search_url = "?search_boardId="
base_url = "http://www.kau.ac.kr/page"
# KAU 공지 할당
gen = "General"
aca = "Academic"
sch = "Scholar"
job = "Career"
eve = "Event"
emp = "Employ"
dor = "Dormitory"

HomeList = [gen, aca, sch, job, eve, emp, dor]

# 일반공지
gen_notice_board = home_url + "/general_list.jsp"
gen_notice_link = gen_notice_board + search_url

# 학사공지
aca_notice_board = home_url + "/academicinfo_list.jsp"
aca_notice_link = aca_notice_board + search_url

# 장학/대출공지
sch_notice_board = home_url + "/scholarship_list.jsp"
sch_notice_link = sch_notice_board + search_url

# 취업공지
job_notice_board = "http://kau.ac.kr/page/kau_media/career_list.jsp"
job_notice_link = job_notice_board + search_url

# 행사공지
eve_notice_board = home_url + "/event_list.jsp"
eve_notice_link = eve_notice_board + search_url

# 모집/채용공지
emp_notice_board = home_url + "/employment_list.jsp"
emp_notice_link = emp_notice_board + search_url

# 생활관
dor_notice_board = base_url + "/web/life/community/notice_li.jsp"
dor_notice_link = dor_notice_board + search_url

# 대문 공지록과 각 공지 주소 연동하는 Dict 생성
HomeDict = {gen: [gen_notice_board, gen_notice_link], \
            aca: [aca_notice_board, aca_notice_link], \
            sch: [sch_notice_board, sch_notice_link], \
            job: [job_notice_board, job_notice_link], \
            eve: [eve_notice_board, eve_notice_link], \
            emp: [emp_notice_board, emp_notice_link], \
            dor: [dor_notice_board, dor_notice_link]}

# 학부 공지 할당
ame = "AME"
etc = "ETC"
avs = "AVS"
sof = "SOF"
atl = "ATL"
bus = "BUS"
aeo = "AEO"

deptlst = [bus, sof, atl, ame, aeo, avs, etc]

# 항우기
ame_notice_board = base_url + "/web/am_engineer/notice/dept_li.jsp"
ame_notice_link = ame_notice_board + search_url
# 항전정
etc_notice_board = base_url + "/dept/etce1/board/notice_li.jsp"
etc_notice_link = etc_notice_board + search_url
# 소프트웨어학과
sof_notice_board = "http://sw.kau.ac.kr/?page_id=739"
sof_notice_link = sof_notice_board + "&mod=document&uid="
# 재료공학과
avs_notice_board = base_url + "/web/aviation_stuff/notice/dept_li.jsp"
avs_notice_link = avs_notice_board + search_url
# 항공교통물류학부
atl_notice_board = base_url + "/web/universe_law/life/notice_li.jsp"
atl_notice_link = atl_notice_board + search_url
# 항공운항학과
aeo_notice_board = base_url + "/web/aviation_service/information/no_dept_li.jsp"
aeo_notice_link = aeo_notice_board + search_url
# 경영학부
bus_notice_board = base_url + "/web/business/community/notice_li.jsp"
bus_notice_link = bus_notice_board + search_url

# 학부목록과 각 학부 웹사이트 연동하는 Dict 생성
DeptDict = {ame: [ame_notice_board, ame_notice_link], \
            etc: [etc_notice_board, etc_notice_link], \
            sof: [sof_notice_board, sof_notice_link], \
            avs: [avs_notice_board, avs_notice_link], \
            atl: [atl_notice_board, atl_notice_link], \
            aeo: [aeo_notice_board, aeo_notice_link], \
            bus: [bus_notice_board, bus_notice_link]}

@app.route('/userinfo', methods=('GET', 'POST'))
def userinfo():
    if request.method == 'POST':
        return 'Sorry, Nothing at this URL.', 404
    elif request.method == 'GET':
        tz = pytz.timezone('Asia/Seoul')
        d = dt.now(tz)
        d = d.replace(tzinfo=None)
        d = d.strftime("%Y/%m/%d")

        body = """<!DOCTYPE html><head><meta charset="utf-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1"></head>
                <body><div style="margin-top:14pt;margin-bottom:14pt;"><font face="Verdana,Arial,Helvetica,sans-serif" size="1">
                <span style="font-size:13px;"><font size="3"><span style="font-size:21px;"><b>일간(""" \
                + d + """) kau-notify 정보</b></span></font><br></span></font></div><hr>"""

        daycount = 0

        TotalSubs = len(Subs.query().fetch(keys_only=True))  #총 구독 인원수

        body += '''<div align="left" style="margin-top:1pt;margin-bottom:1pt;">총 구독자 수: ''' + str(TotalSubs) + ''' 명</div><br><hr>'''

        d = dt.now(tz)
        d = d.replace(tzinfo=None)
        requests_toolbelt.adapters.appengine.monkeypatch()

        def BoardTextDay(board_url, notice_link):
            try:
                source_code = requests.get(board_url,timeout=60)
                plain_text = source_code.text
                soup = BeautifulSoup(plain_text, 'lxml')
                if board_url == sof_notice_board:
                    title = soup.find_all('td', {'class': "kboard-list-title"})
                    title = title[1:]  # 처음 제목 줄 제외
                    datetext = soup.find_all('td', {'class': "kboard-list-date"})
                    datetext = datetext[1:]
                    date_format = "%Y.%m.%d"
                else:
                    title = soup.find_all('td', {'headers': "board_title"})
                    datetext = soup.find_all('td', {'headers': "board_create"})
                    date_format = "%Y-%m-%d"

                daylst = []
                for datedata in datetext:
                    datedata = datedata.get_text()
                    try:
                        datedata = dt.strptime(datedata, date_format)
                    except:
                        datedata = dt.today()
                        datedata = datedata.replace(hour=0, minute=0, second=0, microsecond=0)
                    daylst.append(datedata)

                hreflst = []
                titlelst = []
                for text in title:
                    if board_url != sof_notice_board:
                        GetText = text.get('title')
                    else:
                        realTitle = text.find_all('div', {'class': 'kboard-avatar-cut-strings'})
                        for softext in realTitle:
                            GetText = softext.get_text()
                            GetText = GetText.strip()  # 공백 지우기
                    titlelst.append(GetText.encode('utf-8'))
                    GetLink = text.find_all('a')
                    for atag in GetLink:
                        link = atag.get('href')
                        if board_url != sof_notice_board:
                            boardID = ''.join(s for s in link if s.isdigit())
                        else:
                            board_and_ID = ''.join(s for s in link if s.isdigit())
                            boardID = board_and_ID[3:6]
                        url = notice_link + boardID
                        hreflst.append(url)
                board_count = 0  # 새로운 공지 개수를 위한 변수
                html = ""
                for i in range(len(daylst)):
                    if (d - daylst[i]).days == daycount:
                        r = re.compile(r"(http://[^ ]+)").sub(
                            r'<b>· </b><a href="\1" target="_blank">' + titlelst[i] + '</a><br>',
                            hreflst[i])
                        html += r
                        board_count += 1
                daycal = (d - max(daylst)).days
                return board_count

            except requests.exceptions.RequestException as e:
                logging.info(e)
                # sys.exit(1)
                html = " "
                daycal = 1
                return html, daycal

            except runtime.DeadlineExceededError:
                logging.error('Handling DeadlineExceededError for url: %s' % source_code)
                html = " "
                daycal = 1
                return html, daycal


        HomeNewPost = []
        for board in HomeList:
            count = BoardTextDay(HomeDict[board][0], HomeDict[board][1])
            HomeNewPost.append(count)


        i = 0
        for board in HomeList:
            if HomeNewPost[i]>0:
                body += '''<div align="left" style="margin-top:1pt;margin-bottom:1pt;">''' + BoardDict[board] + ''': ''' + str(
                    HomeNewPost[i]) + ''' 개<br><br>'''
                i += 1
            else:
                i += 1

        DeptNewPost = []
        for dept in deptlst:
            count = BoardTextDay(DeptDict[dept][0], DeptDict[dept][1])
            DeptNewPost.append(count)

        i = 0
        for dept in deptlst:
            if DeptNewPost[i] > 0:
                body += '''<div align="left" style="margin-top:1pt;margin-bottom:1pt;">'''+ BoardDict[dept]+ ''': ''' + str(DeptNewPost[i]) + ''' 개<br><br>'''
                i += 1
            else:
                i += 1

        body += """</body>"""
        sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
        to_email = Email(Developer_Email)
        from_email = Email(SENDGRID_SENDER)
        content = Content('text/html', body)
        subject = "kau-notify 정보 알림"
        message = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=message.get())

        return ('', 204)
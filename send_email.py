# -*- coding: utf-8 -*-
from google.appengine.ext import ndb
from itsdangerous import URLSafeSerializer, BadData
import requests, smtplib, re, os, sys
from datetime import datetime as dt
from datetime import date
from bs4 import BeautifulSoup
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from app import app
import logging, requests_toolbelt.adapters.appengine, lxml
from app.models import *
from app.config import *
from google.appengine.api import mail
import pytz, time
import sendgrid
from app.config import *
from sendgrid.helpers.mail import *
from google.appengine.api import urlfetch

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

base_url = "http://www.kau.ac.kr/page"

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

@app.route('/sendemail', methods=('GET', 'POST'))
def sendemail():
    tz = pytz.timezone('Asia/Seoul')
    d = dt.now(tz)
    d = d.replace(tzinfo=None)
    requests_toolbelt.adapters.appengine.monkeypatch()
    s = URLSafeSerializer(app.secret_key, salt=Noti_Setting_Token)

    daycount = 0  # 오늘 날짜의 게시물을 가져오기 위해 반드시 0이어야만 함

    def BoardTextDay(board_url, notice_link):
        try:
            source_code = requests.get(board_url, timeout=60)
            plain_text = source_code.text
            soup = BeautifulSoup(plain_text, 'lxml')
            if board_url == sof_notice_board:
                title = soup.find_all('td', {'class': "kboard-list-title"})
                title = title[1:]  # 처음 제목 줄 제외
                datetext = soup.find_all('td', {'class': "kboard-list-date"})
                datetext = datetext[1:]  # 날짜 열 상단의 "작성일"이라는 글자도 가져오므로 첫번째 값은 제외
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

            html = ""
            for i in range(len(daylst)):
                if (d - daylst[i]).days == daycount:
                    r = re.compile(r"(http://[^ ]+)").sub(
                        r'<b>· </b><a href="\1" target="_blank">' + titlelst[i] + '</a><br>',
                        hreflst[i])
                    html += r
            daycal = (d - max(daylst)).days
            return html, daycal
        except requests.exceptions.RequestException as e:
            logging.info(e)
            # sys.exit(1)
            html = " "
            daycal = 1
            return html, daycal

    DaycountDict = {}
    daycal_set = set()
    HomeNewPostDict = {}
    # KAU 공지와 학부공지 글과 날짜가져오기
    for board in HomeList:
        text, daycal = BoardTextDay(HomeDict[board][0], HomeDict[board][1])
        DaycountDict[board] = daycal
        HomeNewPostDict[board] = text
        daycal_set.add(daycal)

    DeptNewPostDict = {}
    for dept in deptlst:
        text, daycal = BoardTextDay(DeptDict[dept][0], DeptDict[dept][1])
        DaycountDict[dept] = daycal
        DeptNewPostDict[dept] = text
        daycal_set.add(daycal)


    if request.method == 'POST':
        return '잘못된 접근을 시도하고 있습니다.', 404
    elif request.method == 'GET':
        if daycount in daycal_set:
            qry = Subs.query()
            for user in qry.fetch():
                toaddr = user.email
                token = s.dumps(toaddr)
                url = "https://kau-notify.appspot.com/notificationSettings/" + token

                footer = '''<div style="margin-top:3pt;margin-bottom:3pt;"><font face="Verdana,Arial,Helvetica,sans-serif" size="1">
                       <span style="font-size:13px;">&nbsp;</span></font></div><br><hr><div style="margin-top:10pt;margin-bottom:14pt;">
                       <font face="Verdana,Arial,Helvetica,sans-serif" size="1">
                       <span style="font-size:13px;">이제 공지 알리미를 텔레그램에서 만나보세요. 실시간으로 공지사항이 등록되면 알려드립니다.
                       <a href="https://kau-notify.appspot.com/telegram" target="_blank">한국항공대 공지봇 바로가기</a>
                        </span>
                       <br>
                       <span style="font-size:13px;">더 많은 학우들이 알림을 받을 수 있도록
                       <a href="https://kau-notify.appspot.com/" target="_blank">구독 신청 페이지</a>
                        메뉴에서 페이스북 또는 카카오톡으로 공유하세요!</span>
                       <br>
                       <span style="font-size:13px;">공지사항 알리미 <a href="https://www.facebook.com/kaunotifier" target="_blank">페이스북 페이지</a>
                        에서 서비스 관련 공지를 확인하실 수 있습니다.</span>
                        <br>
                        <span style="font-size:13px;">본 메일은 게시판 알림신청 하신분들에게 발송되는 메일이며 알림 관련 설정은
                       <a href="''' + url + '''" target="_blank">여기</a>서 하실 수 있습니다.</span>
                       <br>
                       <span style="font-size:13px;">기타 문의사항은 <a href="mailto:kaunotifier@gmail.com">kaunotifier@gmail.com</a>
                       으로 연락 바랍니다.</span>
                        </font></div></body>'''

                d = dt.now(tz)
                d = d.replace(tzinfo=None)
                d = d.strftime("%Y/%m/%d")
                body = """<!DOCTYPE html><head><meta charset="utf-8">
                            <meta http-equiv="X-UA-Compatible" content="IE=edge">
                            <meta name="viewport" content="width=device-width, initial-scale=1"></head>
                            <body><div style="margin-top:14pt;margin-bottom:14pt;"><font face="Verdana,Arial,Helvetica,sans-serif" size="1">
                            <span style="font-size:13px;"><font size="3"><span style="font-size:21px;"><b>일간(""" \
                       + d + """) 한국항공대학교 공지사항 새글 모음</b></span></font><br></span></font></div><hr>"""

                # 구독자가 구독한 게시판 중에 새 글이 있는 게시판 개수
                NumOfNewPostBoard = 0
                for board in user.subsboard:
                    if DaycountDict[board.type] == daycount:
                        NumOfNewPostBoard += 1
                for board in user.deptboard:
                    if DaycountDict[board.type] == daycount:
                        NumOfNewPostBoard += 1

                # 구독자 이메일 작성
                i = 0
                for board in user.subsboard:
                    if DaycountDict[board.type] == daycount:
                        i += 1
                        body += """<span style="font-size:19px;"><b>""" + BoardDict[board.type] + """ 공지</b></span><br>
                                    <div align="left" style="margin-top:1pt;margin-bottom:1pt;">""" + HomeNewPostDict[
                            board.type] + """</div>"""
                        if i < NumOfNewPostBoard:
                            body += """<hr>"""
                for board in user.deptboard:
                    if DaycountDict[board.type] == daycount:
                        i += 1
                        body += """<span style="font-size:19px;"><b>""" + BoardDict[board.type] + """ 공지</b></span><br>
                                    <div align="left" style="margin-top:1pt;margin-bottom:1pt;">""" + DeptNewPostDict[
                            board.type] + """</div>"""
                        if i < NumOfNewPostBoard:
                            body += """<hr>"""

                if NumOfNewPostBoard > 0:
                    body += footer
                    sg = sendgrid.SendGridAPIClient(apikey = SENDGRID_API_KEY)
                    to_email = Email(toaddr)
                    from_email = Email(SENDGRID_SENDER)
                    content = Content('text/html', body)
                    subject = "한국항공대학교 오늘의 공지사항 모음"
                    message = Mail(from_email, subject, to_email, content)
                    response = sg.client.mail.send.post(request_body=message.get())
        return ('', 204)

# 모바일 사이트 일반, 학사공지 가져오는 코드
# urllst = []
# baseurl = 'http://m.kau.ac.kr/page/mobile/kauspace/'
# urllst.append(baseurl + 'general_list.jsp')
# urllst.append(baseurl + 'academicinfo_list.jsp')
# gentextlst = []
# genlinklst = []
# acatextlst = []
# acalinklst = []
# def textgen(td, textlst, linklst):
#     datecal = []
#     text = ""
#     for datedata in td:
#         datetxt = datedata.string.encode('utf-8')
#         GetLinkTag = datedata.find_all('a')
#         for link in GetLinkTag:
#             href = baseurl + link.get('href')
#             linklst.append(href)
#         textlst.append(datetxt)
#     datelst = textlst[2::3]
#     titlelst = textlst[1::3]
#
#     date_format = "%Y.%m.%d"
#     for i in datelst:
#         a = datetime.strptime(i, date_format)
#         datecal.append(a)
#     for i in range(len(datecal)):
#         if (d - datecal[i]).days == daycount:
#             r = re.compile(r"(http://[^ ]+)").sub(
#                 r'<b>· </b><a href="\1" target="_blank">' + titlelst[i] + '</a><br>',
#                 linklst[i])
#             text += r
#     daycal = (d - datecal[0]).days
#     return text, daycal
#
#
# for url in urllst:
#     try:
#         source_code = requests.get(url)
#         plain_text = source_code.text
#         soup = BeautifulSoup(plain_text, 'lxml')
#         table = soup.find_all('table', {'class': "tblCom"})
#         td = table[0].find_all('td')
#         if url == urllst[0]:
#             gentext, gendaycal = textgen(td, gentextlst, genlinklst)
#         else:
#             acatext, acadaycal = textgen(td, acatextlst, acalinklst)
#     except requests.exceptions.RequestException as e:
#         logging.info(e)
#         sys.exit(1)
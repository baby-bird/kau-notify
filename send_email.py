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
import pytz, time, json
import sendgrid
from app.config import *
from sendgrid.helpers.mail import *
from google.appengine.api import urlfetch

urlfetch.set_default_fetch_deadline(60)

main_board_id = 1
dept_board_id = 2
career_board_id = 3

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
             "AEO": "항공운항학과", \
             "FRM": "자유전공학부"}

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

HomeLst_txt = [gen, aca, sch, job, eve, emp, dor]

# 일반공지
gen_notice_board = home_url + "/general_list.jsp"
gen_notice_link = gen_notice_board + search_url

# 학사공지
aca_notice_board = home_url + "/academicinfo_list.jsp"
aca_notice_link = aca_notice_board + search_url

# 장학/대출공지
sch_notice_board = home_url + "/scholarship_list.jsp"
sch_notice_link = sch_notice_board + search_url

# 대학일자리센터 공지사항
job_notice_board = "http://career.kau.ac.kr/ko/community/notice2"
job_notice_link = job_notice_board + "/view/"

# 행사공지
eve_notice_board = home_url + "/event_list.jsp"
eve_notice_link = eve_notice_board + search_url

# 모집/채용공지
emp_notice_board = home_url + "/employment_list.jsp"
emp_notice_link = emp_notice_board + search_url

# 생활관
dor_notice_board = base_url + "/web/life/community/notice_li.jsp"
dor_notice_link = dor_notice_board + search_url

class Home:
  def __init__(self, board_url, notice_link, main_board_id):
    self.board_url = board_url
    self.notice_link = notice_link
    self.board_id = main_board_id

# 대문 공지록과 각 공지 주소 연동하는 Instance 생성
gen = Home(gen_notice_board, gen_notice_link, main_board_id)
aca = Home(aca_notice_board, aca_notice_link, main_board_id)
sch = Home(sch_notice_board, sch_notice_link, main_board_id)
job = Home(job_notice_board, job_notice_link, career_board_id)
eve = Home(eve_notice_board, eve_notice_link, main_board_id)
emp = Home(emp_notice_board, emp_notice_link, main_board_id)
dor = Home(dor_notice_board, dor_notice_link, main_board_id)

HomeLst = [gen, aca, sch, job, eve, emp, dor]


base_url = "http://college.kau.ac.kr/web/pages"

# 항우기
ame_notice_board = base_url + "/gc1986b.do"
ame_notice_link = ame_notice_board + "?siteFlag=am_www&bbsFlag=View&"
# 항전정
etc_notice_board = base_url + "/gc23761b.do"
etc_notice_link = etc_notice_board + "?siteFlag=eie_www&bbsFlag=View&"
# 소프트웨어학과
sof_notice_board = base_url + "/gc911b.do"
sof_notice_link = sof_notice_board + "?siteFlag=sw_www&bbsFlag=View&"
# 재료공학과
avs_notice_board = base_url + "/gc46806b.do"
avs_notice_link = avs_notice_board + "?siteFlag=materials_www&bbsFlag=View&"
# 항공교통물류학부
atl_notice_board = base_url + "/gc93464b.do"
atl_notice_link = atl_notice_board + "?siteFlag=attll_www&bbsFlag=View&"
# 항공운항학과
aeo_notice_board = base_url + "/gc61682b.do"
aeo_notice_link = aeo_notice_board + "?siteFlag=hw_www&bbsFlag=View&"
# 경영학부
bus_notice_board = base_url + "/gc25685b.do"
bus_notice_link = bus_notice_board + "?siteFlag=biz_www&bbsFlag=View&"
# 자유전공학부
frm_notice_board = base_url + "/gc46051b.do"
frm_notice_link = frm_notice_board + "?siteFlag=free_www&bbsFlag=View&"

class Dept:
  def __init__(self, board_url, notice_link, dept_board_id, bbsId, siteFlag):
    self.board_url = board_url
    self.notice_link = notice_link
    self.board_id = dept_board_id
    self.bbsId = bbsId
    self.siteFlag = siteFlag

# 학부목록과 각 학부 웹사이트 연동하는 Instance 생성
ame = Dept(ame_notice_board, ame_notice_link, dept_board_id, '0024', 'am_www')
etc = Dept(etc_notice_board, etc_notice_link, dept_board_id, '0015', 'eie_www')
sof = Dept(sof_notice_board, sof_notice_link, dept_board_id, '0032', 'sw_www')
avs = Dept(avs_notice_board, avs_notice_link, dept_board_id, '0096', 'materials_www')
atl = Dept(atl_notice_board, atl_notice_link, dept_board_id, '0048', 'attll_www')
aeo = Dept(aeo_notice_board, aeo_notice_link, dept_board_id, '0003', 'hw_www')
bus = Dept(bus_notice_board, bus_notice_link, dept_board_id, '0056', 'biz_www')
frm = Dept(frm_notice_board, frm_notice_link, dept_board_id, '0072', 'free_www')

DeptLst = [bus, sof, atl, ame, aeo, avs, etc, frm]

# 학부 공지 텍스트 할당
ame = "AME"
etc = "ETC"
avs = "AVS"
sof = "SOF"
atl = "ATL"
bus = "BUS"
aeo = "AEO"
frm = "FRM"

DeptLst_txt = [bus, sof, atl, ame, aeo, avs, etc, frm]


@app.route('/sendemail', methods=('GET', 'POST'))
def sendemail():
    tz = pytz.timezone('Asia/Seoul')
    d = dt.now(tz)
    d = d.replace(tzinfo=None)
    requests_toolbelt.adapters.appengine.monkeypatch()
    s = URLSafeSerializer(app.secret_key, salt=Noti_Setting_Token)

    daycount = 0  # 오늘 날짜의 게시물을 가져오기 위해 반드시 0 이어야만 함

    def BoardTextDay(board):

        if board.board_id == dept_board_id:
            bbsId = board.bbsId
            siteFlag = board.siteFlag

        board_url = board.board_url
        notice_link = board.notice_link
        board_id = board.board_id

        try:
            if board_id == main_board_id or board_id == career_board_id:
                source_code = requests.get(board_url, timeout=60)
                plain_text = source_code.text
                soup = BeautifulSoup(plain_text, 'lxml')

                if board_id == career_board_id:
                    title = soup.find_all('li', {'class': "tbody"})
                    datetext = soup.find_all('span', {'class': "reg_date"})
                    datetext = datetext[1:]  # 날짜 열 상단의 "등록일" 글자도 가져오므로 첫버째 값은 제
                    date_format = "%Y-%m-%d"
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
                    if board_id == career_board_id:
                        GetText = text.find('a').text
                    else:
                        GetText = text.get('title')
                    titlelst.append(GetText.encode('utf-8'))
                    GetLink = text.find_all('a')
                    for atag in GetLink:
                        link = atag.get('href')
                        boardID = ''.join(s for s in link if s.isdigit())
                        if board_id == career_board_id:
                            boardID = boardID[1:-1]
                        url = notice_link + boardID
                        hreflst.append(url)
            else:
                bbsId_str = "bbsId="
                nttId_str = "&nttId="
                payload = {"siteFlag": siteFlag, "bbsId": bbsId, "pageIndex": "1", "bbsAuth": "30"}
                headers = {'Content-Type': 'application/json; charset=utf-8', \
                           'Host': 'college.kau.ac.kr', \
                           'Origin': 'http://college.kau.ac.kr', \
                           'Referer': board_url}
                source_code = requests.post('http://college.kau.ac.kr/web/bbs/bbsListApi.gen', data=json.dumps(payload),
                                           headers=headers, timeout=60)
                plain_text = source_code.text
                result_data = json.loads(plain_text)
                datetext = []
                hreflst = []
                titlelst = []
                for data in result_data['resultList']:
                    titlelst.append(data['nttSj'])
                    hreflst.append(notice_link + bbsId_str + bbsId + nttId_str + str(data['nttId']))
                    datetext.append(data['frstRegisterPnttm'])
                daylst = []
                date_format = "%Y-%m-%d"
                for datedata in datetext:
                    try:
                        datedata = dt.strptime(datedata, date_format)
                    except:
                        datedata = dt.today()
                        datedata = datedata.replace(hour=0, minute=0, second=0, microsecond=0)
                    daylst.append(datedata)

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
    for i in range(len(HomeLst)):
        text, daycal = BoardTextDay(HomeLst[i])
        DaycountDict[HomeLst_txt[i]] = daycal
        HomeNewPostDict[HomeLst_txt[i]] = text
        daycal_set.add(daycal)

    DeptNewPostDict = {}
    for i in range(len(DeptLst)):
        text, daycal = BoardTextDay(DeptLst[i])
        DaycountDict[DeptLst_txt[i]] = daycal
        DeptNewPostDict[DeptLst_txt[i]] = text

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
                       <span style="font-size:13px;">본 메일은 게시판 알림을 구독하신 분들에게 발송되는 메일입니다.</span>
                       <br>
                       <span style="font-size:13px;">게시판 추가/제거및 구독 취소는 
                       <a href="''' + url + '''" target="_blank"><strong>게시판 설정 페이지 링크</strong></a>에서 하실 수 있습니다.</span>
                       <br>
                       <span style="font-size:13px;">더 많은 학우들이 알림을 받을 수 있도록
                       <a href="https://kau-notify.appspot.com/" target="_blank">구독 신청 페이지</a>
                        메뉴에서 페이스북 또는 카카오톡으로 공유하세요!</span>
                       <br>
                       <span style="font-size:13px;">공지사항 알리미 <a href="https://www.facebook.com/kaunotifier" target="_blank">페이스북 페이지</a>
                        에서 서비스 관련 공지를 확인하실 수 있습니다.</span>
                        <br>
                        <span style="font-size:13px;">실시간으로 새로운 공지사항을 알려주는 텔레그램 공지봇도 이용해 보세요.
                       <a href="https://kau-notify.appspot.com/telegram" target="_blank">한국항공대 공지봇 바로가기</a>
                        </span>
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
#-*- coding: utf-8 -*-
from flask import Flask, request,session, redirect, url_for, abort, render_template, flash, send_from_directory
from app.models import *
from app import app
from google.appengine.ext import ndb
import logging

BoardDict = {"항공우주 및 기계공학부": "AME", \
             "항공전자정보공학부": "ETC", \
             "항공재료공학과": "AVS", \
             "소프트웨어학과": "SOF", \
             "항공교통물류학부": "ATL", \
             "경영학부": "BUS", \
             "항공운항학과": "AEO"}

@app.route('/counter', methods=('GET', 'POST'))
def counter():
    counter_qry = Counter.query()
    for c in counter_qry.fetch(1):
        c.counter = 430 #구독자 수 메일 받은 것 기반으로 재설정
        c.put()
    return ('', 204)

# @app.route('/setdb', methods=('GET', 'POST'))
# def setdb():
#     qry = Subs.query()
#     for user in qry.fetch():
#         if user.dept:
#             dept=BoardDict[str(user.dept)]
#             user.subsboard = [
#                 MainBoard(type='General'),
#                 MainBoard(type='Academic'),
#             ]
#             user.deptboard = [
#                 DeptBoard(type=dept)
#             ]
#             user.put()
#     return ('', 204)
#
# @app.route('/removedept', methods=('GET', 'POST'))
# def removedept():
#     qry = Subs.query()
#     for user in qry.fetch():
#         if 'dept' in user._properties:
#             user._clone_properties()
#             del user._properties['dept']
#             user.put()
#     return ('', 204)
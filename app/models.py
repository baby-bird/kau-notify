#-*- coding: utf-8 -*-
import datetime
from google.appengine.ext import ndb

class MainBoard(ndb.Expando):
    type = ndb.StringProperty()  # E.g., '일반', '학사'

class DeptBoard(ndb.Expando):
    type = ndb.StringProperty() # E.g., '항공우주 및 기계공학부', '항공전자공학부'

# 구독자를 Subs테이블에 맵핑
class Subs(ndb.Expando):
    email = ndb.StringProperty(indexed=True, required=True)
    subsboard = ndb.StructuredProperty(MainBoard, repeated=True)
    deptboard = ndb.StructuredProperty(DeptBoard, repeated=True)
    comment = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add = True)
    first_email_check_date = ndb.DateProperty()
    second_email_check_date = ndb.DateProperty()

class Counter(ndb.Expando):
    namespace = ndb.StringProperty(indexed=True, required=True)
    counter = ndb.IntegerProperty(indexed=True, required=True)

class Unsubs(ndb.Expando):
    date = ndb.DateTimeProperty(auto_now=True)

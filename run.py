#!flask/bin/python
#-*- coding: utf-8 -*-
from app.config import *
from app import app

app.secret_key = app_secret_key

if __name__ == '__main__':
    app.run()
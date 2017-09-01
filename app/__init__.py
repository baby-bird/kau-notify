from flask import Flask
from config import *

app = Flask(__name__)
app.secret_key = app_secret_key

from app import controllers

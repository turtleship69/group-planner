"""website to show when 2 or mroe people are free at the same time
ask user for their availability, with a calendar, either asking for blacklisted times or whitelisted times
user then gets a url they can share with others, and others can add their availability
when all users have added their availability, the website will show when everyone is free"""

from asyncio import events
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from datetime import datetime, timedelta, date, time, timezone
from dateutil import tz
import hashlib

from pprint import pprint

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


#create a 2d array of all the timeslots
#first list is the days of the week, second list is every hour of the day
TIMESLOTS = [[0]*24]*7

pprint(TIMESLOTS)

database = {}

count = 0


@app.route("/")
def index():
    return render_template("home.html")

"""create a new event
ask user for name, and brief description
ask user for their availability, with a calendar, either asking for blacklisted times or whitelisted times
if the user is asking for blacklisted times, all times the user selects will be marked as unavailable
if the user is asking for whitelisted times, all times the user doesn't select will be marked as unavailable
save the event and the user's availability to the database
user then gets a url they can share with others starting with /event/ and the event id"""
@app.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        """example json data
        {
            "name":"name",
            "description":"description",
            "blacklist":true,
            availability:["0,0", "23,6"]
        }
        """
        data = request.get_json()
        #create a new event
        #hash count using crc to get a unique id and increment count by 1
        event_id = hashlib.crc32(str(count).encode()).hexdigest()
        count += 1

        #create a copy of the timeslots array, and for every time the user is unavailable, set the value to 1
        event_timeslots = TIMESLOTS.copy()
        for time in data["availability"]:
            time = time.split(",")
            event_timeslots[int(time[0])][int(time[1])] = 1

        #create a new event in the database
        database[event_id] = {"name":data["name"], "description":data["description"], "blacklist":data["blacklist"], "timeslots":event_timeslots}

        pprint(database)

        return event_id
        
    else:
        return render_template("new.html")



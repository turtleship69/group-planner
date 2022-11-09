"""website to show when 2 or mroe people are free at the same time
ask user for their availability, with a calendar, either asking for blacklisted times or whitelisted times
user then gets a url they can share with others, and others can add their availability
when all users have added their availability, the website will show when everyone is free"""

from flask import Flask, render_template, request, session, make_response
from flask_session import Session
from os import urandom
import binascii
from json import dumps, loads
from pprint import pprint

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_COOKIE_HTTPONLY'] = False

app.secret_key = urandom(16)

Session(app)


#create a 2d array of all the timeslots
#first list is the days of the week, second list is every hour of the day
TIMESLOTS = [[0 for i in range(24)] for j in range(7)] # [[12am-11pm]mon-sun]
DEVELOPER = False

def debugOut(msg):
    global DEVELOPER
    if DEVELOPER:
        print(msg)

database = {}

count = 0

@app.route("/")
def index():
    if DEVELOPER:
        resp = make_response(dumps(database))
        #add json header
        resp.headers['Content-Type'] = 'application/json'
        pprint(TIMESLOTS)
        return resp
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
        global count
        event_id = binascii.crc32(str(count).encode())
        count += 1

        #create a copy of the timeslots array, and for every time the user is unavailable, set the value to 1
        event_timeslots = [[0 for i in range(24)] for j in range(7)]#TIMESLOTS[:]
        if not data["blacklist"]:
            debugOut("whitelist")
            #pprint(data["availability"])
            for time in data["availability"]:
                timeList = time.split(",")
                event_timeslots[int(timeList[0])][int(timeList[1])] = 1
        else:
            debugOut("blacklist")
            for i in range(7):
                for j in range(24):
                    if f"{i},{j}" in data["availability"]:
                        event_timeslots[i][j] = 0
                    else:
                        event_timeslots[i][j] = 1

        #create a new event in the database
        #add users session id to the list of users who've signed up
        database[str(event_id)] = {
            "name":data["name"],
            "description":data["description"],
            #"blacklist":data["blacklist"],
            "timeslots":event_timeslots,
            "users":[data["session"]]
        }

        #pprint(database[str(event_id)]["timeslots"])

        return str(event_id)
        
    else:
        #check if there is already a persistent cookie and if not, add one
        if "session" not in session:
            session["session"] = binascii.b2a_hex(urandom(15)).decode("utf-8")
        return render_template("new.html")


"""show the event
ask user for their availability, with a calendar, either asking for blacklisted times or whitelisted times
if the user is asking for blacklisted times, all times the user selects will be marked as unavailable
if the user is asking for whitelisted times, all times the user doesn't select will be marked as unavailable
save the user's availability to the database
when 2 or more users have added their availability, the website will show when everyone is free
when a 3rd person or more adds their availability, the website update"""
@app.route("/event/<event_id>", methods=["GET", "POST"])
def event(event_id):
    if request.method == "POST":
        """example json data
        {
            "blacklist":true,
            availability:["0,0", "23,6"]
        }
        """
        data = request.get_json()
        #update the event
        #for every time the user is unavailable, set the value to 1
        if data["blacklist"]:
            for time in data["availability"]:
                timeList = time.split(",")
                timeList = [int(timeList[0]), int(timeList[1])]
                debugOut(timeList)
                if database[event_id]["timeslots"][timeList[0]][timeList[1]] == 1:
                    database[event_id]["timeslots"][timeList[0]][timeList[1]] = 0
        else:
            for i in range(7):
                for j in range(24):
                    if f"{i},{j}" in data["availability"] and database[event_id]["timeslots"][i][j] == 1:
                        database[event_id]["timeslots"][i][j] = 1
                    else:
                        database[event_id]["timeslots"][i][j] = 0
        #add users session id to the list of users who've signed up
        database[event_id]["users"].append(data["session"])

        #pprint(database[event_id]["timeslots"])

        return "success"
        
    else:
        #check if there is already a persistent cookie and if not, add one
        eventDetails = {"name":database[event_id]["name"], "description":database[event_id]["description"]}
        debugOut(request.cookies.get("session"))
        join = make_response(render_template("eventJoin.html", **eventDetails))
        if not request.cookies.get("session"):
            #request.cookies.get("session") = binascii.b2a_hex(urandom(15)).decode("utf-8")
            join.set_cookie("session", binascii.b2a_hex(urandom(15)).decode("utf-8"))
        if request.cookies.get("session") not in database[event_id]["users"]:
            return join
        #make a list of all the timeslots that are available in the form [[0,0],[0,1],[0,2]]
        availableTimes = []
        for i in range(7):
            for j in range(24):
                if database[event_id]["timeslots"][i][j] == 1:
                    availableTimes.append([i,j])
        #pprint(availableTimes)
        return render_template("eventTimes.html", availability=availableTimes)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
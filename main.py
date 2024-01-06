from ics import Calendar, Event
import webuntis as wu
import datetime
import sys
import toml
import requests
import json
import re

class Config:
    def __init__(self, server, username, password, schoolclass, school):
        self.server = server
        self.username = username
        self.password = password
        self.schoolclass = schoolclass
        self.school = school


def getFirstDay(schoolyear):
    #Return current monday

    return schoolyear.start

def getLastDay(schoolyear):
    #Return last day of current schoolyear

    return schoolyear.end

def getCurrentSchoolyear(session):
    year = session.schoolyears()
    return year.filter(id=year.current.id)[0]

def getStudentId(id, config):
    session = requests.Session()

    req = session.get('https://{}/WebUntis/api/public/timetable/weekly/pageconfig?type=5'.format(config.server),
                cookies = {'JSESSIONID': id})

    req_json = json.loads(req.text)

    return req_json['data']['elements'][0]['id']



def getTimetable(student, schoolyear, session):
    #Return timetable object of webuntis api

    #return session.timetable(student=student, start=getFirstDay(schoolyear), end=getLastDay(schoolyear))
    return session.timetable_extended(student=student, start=getFirstDay(schoolyear), end=getLastDay(schoolyear))


def getCalendar(session, timetable):
    #Return Calendar object with events(subjects) from webuntis

    calendar = Calendar()

    for i in range(len(timetable)):
        print(timetable[i])
        subject = timetable[i].subjects
        start = timetable[i].start
        end = timetable[i].end
        cat = str(timetable[i].code) #cancelled oder normal
        try:
            room = str(timetable[i].rooms)
        except IndexError:
            room = "n/a"
        #cat = str(timetable[i].activityType)
        x = timetable[i].studentGroup.split('_')
        teacher = x[len(x)-1] # timetable[i].teacher
        #print(cat)
        if cat == "None":
            cat="U"
        elif cat == "cancelled":
            cat="F"
        elif cat == "irregular":
            cat = "i"
        else:
            print(cat)
        #elif str(cat) == "Cancelled":
        #    cat="C"
        #elif cat == ""

        if len(subject) > 0:
            event = createEvent(subject[0], start, end, room, teacher, cat)
            calendar.events.add(event)
    return calendar

def createEvent(subject, start, end, room, teacher, cat):
    #Return Event object

    event = Event()
    event.name = str(subject)
    event.location = room.strip("[]")
    event.organizer = teacher
    event.description = teacher
    event.categories = cat
    if cat == "F":
        event.status = "CANCELLED"
    event.begin = start + datetime.timedelta(hours=-2)
    event.end = end + datetime.timedelta(hours=-2)

    return event

def createICSFile(calendar, filename):
    f = open(filename, 'w')
    f.write(re.sub(r'\n+', '', str(calendar)).strip('\n'))
    f.close()
    #with open(filename, 'w') as f:
    #    f.writelines(calendar)

def readTOMLFile(filename):
    #Return Config object

    toml_string = ""
    with open(filename, 'r') as f:
        toml_string = toml_string + f.read()

    parsed_toml = toml.loads(toml_string)
    user = parsed_toml["user"]

    return Config(user["server"],user["username"],user["password"],
                  user["class"],user["school"])

def getSession(config):
    #Return Session object

    session = wu.Session(
        server = config.server,
        username = config.username,
        password = config.password,
        school = config.school,
        useragent = 'webuntis-ics-calendar'
    )

    return session

def main():
    #config = readTOMLFile(sys.argv[1])
    config = readTOMLFile("config.toml")

    session = getSession(config)
    session.login()

    schoolyear = getCurrentSchoolyear(session)
    student = getStudentId(session.config['jsessionid'], config)

    timetable = getTimetable(student, schoolyear, session)
    #print(session.exams(start=getFirstDay(schoolyear), end=getLastDay(schoolyear)))
    #print(timetable)

    calendar = getCalendar(session, timetable)
    createICSFile(calendar, "webuntis-timetable.ics")

    session.logout()

main()

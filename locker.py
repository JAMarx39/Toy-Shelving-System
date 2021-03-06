import os
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from werkzeug import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
import datetime

app = Flask(__name__)

from model import db, User, Scanner, Class, Item, Pattern, Alert, Messages

SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'model.db')

app.config.from_object(__name__)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'Smart.Locker.Group.5@gmail.com'
app.config['MAIL_PASSWORD'] = 'Stuff9988'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

db.init_app(app)

scheduleTime = ["07:00"]
schedulePresent = ["true"]

defaultPatternTime = ['07:00']
defaultPatternPresent = ['true']

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    db.create_all()
    db.session.add(
        User(username='ADMIN', email = 'A@A', password=generate_password_hash('ADMIN'),
             firstName='ADMIN', lastName='ADMIN', userType='a'))
    db.session.commit()
    print('Initialized the database.')


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.filter_by(id=session['user_id']).first()


@app.route('/')
def home():
    return render_template("home.html", user=g.user)


@app.route('/login/', methods=["GET", "POST"])
def login():
    error = None

    if g.user:
        return redirect(url_for('home'))

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user.password, request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user.id
            return redirect(url_for('home'))

    return render_template("login.html", error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    error = None
    if request.method == 'POST':
        rv = User.query.filter_by(username=request.form['username']).first()
        error = None
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                        '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['fName']:
            error = 'You have to enter your first name'
        elif not request.form['lName']:
            error = 'You have to enter your last name'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif rv is not None:
            error = 'The username is already taken'
        else:
            if g.user:
                db.session.add(
                    User(username=request.form['username'], email=request.form['email'],
                         password=generate_password_hash(request.form['password']),
                         firstName=request.form['fName'], lastName=request.form['lName'], userType='t'))
                db.session.commit()
                flash('You successfully created a teacher account')
            else:
                db.session.add(
                    User(username=request.form['username'], email=request.form['email'],
                         password=generate_password_hash(request.form['password']),
                         firstName=request.form['fName'], lastName=request.form['lName'], userType='s'))
                db.session.commit()
                flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', user=g.user, error=error)


@app.route('/items', methods=["GET", "POST"])
def items():
    error = None
    if request.method == 'POST':
        error = None
        if not request.form['name']:
            error = 'You have to enter a item name'
        elif not request.form['rfidNum']:
            error = 'You have to enter the RFID number'
        else:
            db.session.add(
                Item(name=request.form['name'], tagID=request.form['rfidNum'], userID=session['user_id'], status=0))
            db.session.commit()
            items = Item.query.filter_by(userID=session['user_id'], name=request.form['name'],
                                         tagID=request.form['rfidNum']).first()

            db.session.add(
                Pattern(userID=session['user_id'], itemID=items.id, dayOfWeek='Monday',
                        startTime=','.join(defaultPatternTime), presentItems=','.join(defaultPatternPresent))
            )
            db.session.add(
                Pattern(userID=session['user_id'], itemID=items.id, dayOfWeek='Tuesday',
                        startTime=','.join(defaultPatternTime), presentItems=','.join(defaultPatternPresent))
            )
            db.session.add(
                Pattern(userID=session['user_id'], itemID=items.id, dayOfWeek='Wednesday',
                        startTime=','.join(defaultPatternTime), presentItems=','.join(defaultPatternPresent))
            )
            db.session.add(
                Pattern(userID=session['user_id'], itemID=items.id, dayOfWeek='Thursday',
                        startTime=','.join(defaultPatternTime), presentItems=','.join(defaultPatternPresent))
            )
            db.session.add(
                Pattern(userID=session['user_id'], itemID=items.id, dayOfWeek='Friday',
                        startTime=','.join(defaultPatternTime), presentItems=','.join(defaultPatternPresent))
            )

            db.session.commit()
            items2 = Pattern.query.filter_by(userID=session['user_id'], itemID=items.id).all()

            for item in items2:
                print(item.startTime)
            flash('You were successfully added an item')
    items = Item.query.filter_by(userID=session['user_id']).all()
    return render_template("items.html", user=g.user, error=error, items=items)


@app.route('/status', methods=["GET", "POST"])
def status():
    items = Item.query.filter_by(userID=session['user_id']).all()
    return render_template("status.html", user=g.user, items=items)


@app.route('/schedule', methods=["GET", "POST"])
def schedule():
    error = None
    if request.method == 'POST':
        error = None
        if not request.form['code']:
            error = 'You have to enter a course code'
        else:
            student = User.query.filter_by(id=session['user_id']).first()
            course = Class.query.filter_by(code=request.form['code']).first()
            if course is not None:
                course.students.append(student)
                student.classes.append(course)
                db.session.commit()

                flash('You successfully added a course')
            else:
                error = 'Not a valid course code'

    student = User.query.filter_by(id=session['user_id']).first()
    return render_template("schedule.html", user=g.user, error=error, classes=student.classes)


@app.route('/notifications')
def notifications():
    student = User.query.filter_by(id=session['user_id']).first()
    courses = student.classes
    messages = []
    for course in courses:
        for message in course.messages:
            messages.append((message, course.name))
    return render_template("notifications.html", user=g.user, notifications=messages)


@app.route('/classes', methods=["GET", "POST"])
def classes():
    error = None
    if request.method == 'POST':
        error = None
        if not request.form['code']:
            error = 'You have to enter a course code'
        elif not request.form['message']:
            error = 'You did not enter an alert'
        else:
            teacher = User.query.filter_by(id=session['user_id']).first()
            course = Class.query.filter_by(code=request.form['code']).first()
            if course.teacherID == teacher.id:
                message = Messages(message=request.form['message'], code=course.code)
                sendEmail(course, request.form['message'])
                course.messages.append(message)
                db.session.add(message)
                db.session.commit()
                flash('You successfully sent an alert')
            else:
                error = 'Not a valid course code'
    classlist = Class.query.filter_by(teacherID=session['user_id']).all()
    return render_template("classes.html", user=g.user, error=error, classes=classlist)


@app.route('/register_class', methods=["GET", "POST"])
def register_class():
    error = None
    if request.method == 'POST':
        error = None
        if not request.form['className']:
            error = 'You have to enter a class name'
        elif not request.form['code']:
            error = 'You have to enter a course code'
        elif not request.form['teacherName']:
            error = 'You have to enter a teacher\'s name'
        elif not request.form['startHours'] or not request.form['startHours']:
            error = 'You have to enter the start time'
        elif not request.form['endHours'] or not request.form['endHours']:
            error = 'You have to enter the end time'
        else:
            teacher = User.query.filter_by(username=request.form['teacherName']).first()
            if teacher and teacher.userType == "t":
                timeStart = request.form['startHours'] + request.form['startHours']
                timeEnd = request.form['endHours'] + request.form['endHours']
                if timeStart < timeEnd:
                    db.session.add(
                        Class(name=request.form['className'], code=request.form['code'], teacherID=teacher.id,
                              startTime=timeStart, endTime=timeEnd))
                    db.session.commit()
                    flash('You were successfully added a class')
                else:
                    error = "The end time must be later than the start time"
            else:
                error = "That teacher username does not exist"
    teachers = User.query.filter_by(userType='t').all()
    return render_template("register_class.html", user=g.user, error=error, teachers=teachers)


@app.route('/updateSchedule', methods=["GET", "POST"])
def update_schedule():
    error = None
    items = Item.query.filter_by(userID=session['user_id']).all()
    schedules = Pattern.query.filter_by(userID=session['user_id']).all()

    if request.method == "POST":

        time = request.form["startHours"] + ":" + request.form["startMinutes"]

        pattern = Pattern.query.filter_by(userID=session['user_id'], itemID=request.form["item"], dayOfWeek=request.form["dayOfWeek"]).first()

        scheduleTime = pattern.startTime.split(",")
        schedulePresent = pattern.presentItem.split(",")

        print(scheduleTime)
        print(schedulePresent)
        print(time)

        found = binarySearch(scheduleTime, 0, len(scheduleTime) - 1, time)
        print(found)

        if found >= 0:
            schedulePresent[found] = request.form["found"]
        else:
            tempTime, tempPresent = updatePattern(scheduleTime, schedulePresent, request.form["found"], time)

            start = 0

            while start < len(tempTime):
                scheduleTime[start] = tempTime[start]
                schedulePresent[start] = tempPresent[start]
                start = start + 1

            print(scheduleTime)
            print(schedulePresent)

        pattern.startTime = ','.join(scheduleTime)
        pattern.presentItem = ','.join(schedulePresent)
        db.session.commit()

        schedules = Pattern.query.filter_by(userID=session['user_id']).all()

    return render_template("updateSchedule.html", error=error, items=items, user=g.user, schedules=schedules)


@app.route('/checkStatus', methods=["GET", "POST"])
def check_time_status():
    error = None
    items = Item.query.filter_by(userID=session['user_id']).all()

    if request.method == "POST":

        time = request.form["Hours"] + ":" + request.form["Minutes"]
        day = request.form["dayOfWeek"]

        pattern = Pattern.query.filter_by(userID=session['user_id'], itemID=request.form["item"],
                                          dayOfWeek=request.form["dayOfWeek"]).first()

        scheduleTime = pattern.startTime.split(",")
        schedulePresent = pattern.presentItem.split(",")

        found = binarySearch(scheduleTime, 0, len(scheduleTime) - 1, time)

        item = Item.query.filter_by(userID=session['user_id'], id=request.form['item']).first()
        data = request.form["found"]

        if found >= 0:
            if data == schedulePresent[found]:
                print("No Problem!")
            else:
                if data == "true":
                    str1 = "Item " + item.name + " had a problem.  You needed it for class."
                else:
                    str1 = "Item " + item.name + " had a problem.  It is missing from the locker."
                sendEmailAlert(str1)
                db.session.add(
                    Alert(userID=session['user_id'], itemID=request.form['item'], message=str1, dayOfWeek=day,
                          time=time, status=1)
                )
                db.session.commit()
                print("There was a problem!")
        else:
            res = findSpot(scheduleTime, time)
            print(res)
            if data == schedulePresent[res]:
                print("No Problem!")
            else:
                if data == "true":
                    str1 = "Item " + item.name + " had a problem.  You needed it for class."
                else:
                    str1 = "Item " + item.name + " had a problem.  It is missing from the locker."
                sendEmailAlert(str1)
                db.session.add(
                    Alert(userID=session['user_id'], itemID=request.form['item'], message=str1, dayOfWeek=day,
                          time=time, status=1)
                )
                db.session.commit()
                print("There was a problem!")

    return render_template("check.html", error=error, items=items, user=g.user)


@app.route("/alerts", methods=["GET", "POST"])
def alerts():
    error = None
    allAlerts = Alert.query.filter_by(userID=session['user_id']).all()
    alertNotHandled = Alert.query.filter_by(userID=session['user_id'], status=1).all()
    alertUserApproved = Alert.query.filter_by(userID=session['user_id'], status=2).all()
    alertForConcern = Alert.query.filter_by(userID=session['user_id'], status=3).all()
    items = Item.query.filter_by(userID=session['user_id']).all()

    if request.method == "POST":
        alert = request.form['item']
        status = request.form['found']

        print(alert)
        print(status)

        alertUpdate = Alert.query.filter_by(id=alert).first()
        alertUpdate.status = int(status)
        db.session.commit()

        counting = Alert.query.filter_by(userID=session['user_id'], itemID=alertUpdate.itemID,
                                         dayOfWeek=alertUpdate.dayOfWeek, time=alertUpdate.time,
                                         status=alertUpdate.status).all()
        print(len(counting))

        if len(counting) >= 3:
            print("Updating Schedule...")
            flash('Schedule was Updated.  Go to Schedule Page to see the new version.')
            pattern = Pattern.query.filter_by(userID=session['user_id'], itemID=alertUpdate.itemID,
                                              dayOfWeek=alertUpdate.dayOfWeek).first()

            scheduleTime = pattern.startTime.split(",")
            schedulePresent = pattern.presentItem.split(",")

            print(scheduleTime)
            print(schedulePresent)

            found = binarySearch(scheduleTime, 0, len(scheduleTime) - 1, alertUpdate.time)
            print(found)

            f2 = "false"
            if "missing" not in alertUpdate.message:
                f2 = "true"
            else:
                f2 = "false"

            if found >= 0:
                schedulePresent[found] = f2
            else:
                tempTime, tempPresent = updatePattern(scheduleTime, schedulePresent, f2, alertUpdate.time)

                start = 0

                while start < len(tempTime):
                    scheduleTime[start] = tempTime[start]
                    schedulePresent[start] = tempPresent[start]
                    start = start + 1

                print(scheduleTime)
                print(schedulePresent)

                pattern.startTime = ','.join(scheduleTime)
                pattern.presentItem = ','.join(schedulePresent)
                db.session.commit()

        allAlerts = Alert.query.filter_by(userID=session['user_id']).all()
        alertNotHandled = Alert.query.filter_by(userID=session['user_id'], status=1).all()
        alertUserApproved = Alert.query.filter_by(userID=session['user_id'], status=2).all()
        alertForConcern = Alert.query.filter_by(userID=session['user_id'], status=3).all()
        items = Item.query.filter_by(userID=session['user_id']).all()

    return render_template("alerts.html", error=error, allAlerts=allAlerts, alertNotHandled=alertNotHandled,
                           alertUserApproved=alertUserApproved, alertForConcern=alertForConcern, user=g.user,
                           items=items)


@app.route("/rfidData", methods=["POST"])
def handleRfidData():
    if request.method == "POST":
        data = request.form['rfid']
        data = data[1:13]
        item = Item.query.filter_by(tagID=data).first()
        if item is not None:
            if item.status == 0:
                item.status = 1
            else:
                item.status = 0
            db.session.commit()

            day = weekdays[datetime.datetime.today().weekday()]
            print(day)

            time = str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute)

            pattern = Pattern.query.filter_by(itemID=item.id, dayOfWeek=day).first()

            scheduleTime = pattern.startTime.split(",")
            schedulePresent = pattern.presentItem.split(",")

            print(scheduleTime)
            print(schedulePresent)

            found = binarySearch(scheduleTime, 0, len(scheduleTime) - 1, time)
            print(found)

            if item.status == 0:
                stat = 'false'
            else:
                stat = 'true'

            if found >= 0:
                if stat == schedulePresent[found]:
                    print("No Problem!")
                else:
                    if item.status == 0:
                        str1 = "Item " + item.name + " had a problem.  You needed it for class."
                    else:
                        str1 = "Item " + item.name + " had a problem.  It is missing from the locker."
                    recip = User.query.filter_by(id=item.userID).first()
                    # sendEmailAlert(str1, recip)
                    db.session.add(
                        Alert(userID=item.userID, itemID=item.id, message=str1, dayOfWeek=day,
                              time=time, status=1)
                    )
                    db.session.commit()
                    print("The was a problem!")
            else:
                res = findSpot(scheduleTime, time)
                print(res)
                if stat == schedulePresent[res]:
                    print("No Problem!")
                else:
                    if item.status == 1:
                        str1 = "Item " + item.name + " had a problem.  You needed it for class."
                    else:
                        str1 = "Item " + item.name + " had a problem.  It is missing from the locker."
                    recip = User.query.filter_by(id=item.userID).first()
                    # sendEmailAlert(str1, recip)
                    db.session.add(
                        Alert(userID=item.userID, itemID=item.id, message=str1, dayOfWeek=day,
                              time=time, status=1)
                    )
                    db.session.commit()
                    print("The was a problem!")

    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('home'))


def updatePattern(times, presentStatus, found, time):
    i = 0

    spot = 0;
    while i < len(times):
        if i < len(times) - 2:
            if (times[i] < time) and (times[i + 1] > time):
                print("check two items")
                print(times[i])
                print(time)
                print(times[i+1])
                print(times[i] < time)
                print(times[i + 1] > time)
                times.insert(i + 1, time)
                presentStatus.insert(i + 1, found)
        else:
            if times[i] < time:
                print("check one item")
                print(times[i])
                print(time)
                print(times[i] <= time)
                spot = i + 1

        i = i + 1
        print(i)

    times.insert(spot, time)
    presentStatus.insert(spot, found)
    return times, presentStatus


def binarySearch(arr, l, r, x):
    while l <= r:
        mid = l + (r - l) // 2
        print(arr[l])
        print(r)
        print(x)
        if l == 0 and r == 0:
            if arr[l] == x:
                return l
            else:
                return -1

        # Check if x is present at mid
        if arr[mid] == x:
            return mid
        # If x is greater, ignore left half
        elif arr[mid] < x:
            l = mid + 1
        # If x is smaller, ignore right half
        else:
            r = mid - 1

    # If we reach here, then the element
    # was not present
    return -1


def findSpot(inputArr, key):
    start = 0

    print(len(inputArr))
    while start < len(inputArr):
        if inputArr[start] < key:
            if (start + 1) == len(inputArr):
                return start
            if inputArr[start + 1] > key:
                return start
        start = start + 1

    return -1


def sendEmail(course, message):
     for student in course.students:
        msg = Message('Message from ' + course.name, sender='Smart.Locker.Group.5@gmail.com', recipients=[student.email])
        msg.body = message
        mail.send(msg)


def sendEmailAlert(alert, recip=None):
    if recip is None:
        recip = g.user
    msg = Message('Alert from Smart Locker', sender='Smart.Locker.Group.5@gmail.com',
                  recipients=[recip.email])
    msg.body = alert
    mail.send(msg)


if __name__ == '__main__':
    ip = '127.0.0.1'
    # ip = '192.168.43.46'
    app.run(host=ip, port='1234')

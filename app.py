from flask import Flask, flash, redirect, render_template, request
from flask_session import Session
import os
import helpers
import sqlite3


# Configure application
app = Flask(__name__)

# Set folder locations and allowed file types
APP_FOLDER_PATH = os.getcwd()
DATABASE_FILE = APP_FOLDER_PATH + '/chat.db'
STATIC_FOLDER = APP_FOLDER_PATH + '/static'
ALLOWED_EXTENSIONS = {'txt'}

# Set flask configuration values
app.config['STATIC_FOLDER'] = STATIC_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Confirm uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.split('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    """ Upload and parse chat file into SQLite3 database """
    if request.method == "POST":
        # Check if the post request has the file part (didn't fail)
        if 'file' not in request.files:
            flash('Upload failed')
            return redirect("/")
        file = request.files['file']

        # Check if user actually submitted anything
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Check if file is of the allowed type
        if file and allowed_file(file.filename):
            # Create secure filename to prevent hacks
            filename = 'chat.txt'
            # Save file to upload folder
            file.save(os.path.join(app.config['STATIC_FOLDER'], filename))

        # Connect to SQLite database
        conn = sqlite3.connect(DATABASE_FILE)
        db = conn.cursor()

        # Open uploaded file and read it into a variable
        with open(os.path.join(app.config['STATIC_FOLDER'], filename), 'r') as f:
            raw_chat = f.read().split("\n")

        # Parse raw chat
        chat = helpers.parse_chat(raw_chat)

        # Populate 'chat' database with message data
        for item in chat:
            db.execute("INSERT INTO chat (date, day, time, author, message, words, emoji) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (item['date'], item['day'], item['time'], item['author'], item['message'], item['words'], item['emoji']))
        conn.commit()

        return redirect("/charts")

    # If connected using GET then delete the database/chat/wordcloud picture, reset the counter to 0 and request a new file
    else:
        # Connect to SQLite database
        conn = sqlite3.connect(DATABASE_FILE)
        db = conn.cursor()

        # Delete data from table
        db.execute("DELETE FROM chat")
        conn.commit()

        # Reset id counter in table
        db.execute("UPDATE SQLITE_SEQUENCE SET SEQ=0 WHERE NAME='chat'")
        conn.commit()

        # Delete all chat files and wordcloud pics
        cloudpicpath = STATIC_FOLDER + '/wordcloud.png'
        chatfile = STATIC_FOLDER + '/chat.txt'
        if os.path.exists(cloudpicpath):
            os.remove(cloudpicpath)
        if os.path.exists(chatfile):
            os.remove(chatfile)

        return render_template("index.html")


@app.route("/charts", methods=["GET"])
def charts():
    # Connect to SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    db = conn.cursor()

    # Check whether database has data, if not then return to upload screen
    db.execute("SELECT count(*) FROM chat")
    datacheck = db.fetchall()
    if datacheck[0][0] == 0:
        return render_template("index.html")

    # Create emojis data for graphs
    db.execute("SELECT emoji FROM chat WHERE emoji!=''")
    # fetchall() returns a list of tuples
    rows = db.fetchall()
    # Create list of tuples of top 20 emoji
    emoji_count = helpers.emoji_list(rows)

    # Messages per day for graphs
    db.execute("SELECT date AS Date, COUNT(*) AS Messages FROM chat GROUP BY date")
    rows = db.fetchall()
    messages_dates = helpers.messages_per_day(rows)

    # Create number of messages sent per author data for graphs
    db.execute("SELECT author, COUNT(author) FROM chat GROUP BY author")
    rows = db.fetchall()
    authorData = helpers.author_count(rows)

    # Create reply time data for 1 hour replies
    db.execute("SELECT author, date, time FROM chat")
    rows = db.fetchall()
    authorsDelta = []
    for i in range(1, len(authorData)):
        time_delta = helpers.reply_time(rows, authorData[i][0], 3600)
        authorsDelta.append([authorData[i][0], time_delta])
    fastestreply = helpers.fastestauthor(authorsDelta)

    # Create number of messages
    db.execute("SELECT COUNT(*) FROM chat")
    rows = db.fetchall()
    nummessages = rows[0][0]

    # Create total duration of chat
    db.execute("SELECT MAX(date), MIN(date) FROM chat")
    rows = db.fetchall()
    chatlength = helpers.daterange(rows)

    # Generate wordcloud image
    db.execute("SELECT message FROM chat")
    rows = db.fetchall()
    commonword = helpers.wordcloudgen(rows, STATIC_FOLDER)

    # Generate list of authors
    authors = ''
    for i in range(1, len(authorData)):
        authors += ' ' + authorData[i][0] + ','

    # Generate word data
    db.execute("SELECT AVG(words), SUM(words) FROM chat")
    rows = db.fetchall()
    word_data = [round(rows[0][0]), rows[0][1]]
    db.execute("SELECT count(message) FROM chat GROUP BY date")
    rows = db.fetchall()
    counter = 0
    for i in rows:
        counter += i[0]
    word_data.append(round(counter/len(rows)))

    return render_template("charts.html",
                           emoji_count=emoji_count, messages_dates=messages_dates, authorData=authorData,
                           authorDelta=authorsDelta,
                           nummessages=nummessages,
                           chatlength=chatlength,
                           fastestreply=fastestreply,
                           authors=authors[:-1],
                           commonword=commonword,
                           word_data=word_data)


if __name__ == "__main__":
    os.system("open http://localhost:8080")
    app.run(debug=True,
            host="0.0.0.0",
            port=8080,
            use_reloader=False)

from datetime import datetime, timedelta
from collections import Counter
import regex
import emoji
import pandas as pd
from wordcloud import WordCloud

# Inspiration from Mazin Ahmed (mazin[at]mazinahmed.net) - https://github.com/mazen160/whatsapp-chat-parser 

"""SET GLOBAL PARAMETERS"""
# Regular expression search
# match 1 = full message, group 1 = date+time, group 2 = date, group 3 = time, group 4 = author, group 5 = message
FULL_MESSAGE = """(\[([\d/]+), ([\d:]+.{3})\]) (.+?): (.+)"""

# Regex for date, eg: [14/7/2019, 4:52:08 pm]
REGEX_DATE = """\[[\d/]+, [\d:]+.{3}\]"""

# Whatsapp first message
START_MESSAGE = 'Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.'

# List of stopwords
STOPWORDS = ['because', 'their', "you're", 'here', "that'll", 'video omitted', 'we', 
            '\x0c', 'this', 'whom', 'who', 'yours', 'she', 'from', '^', "won't", 'are',
            'them', 'image', 'n', 'ours', 'its', 'no', 'before', 'an', 'wouldn', 'above',
            "shan't", 'k', 'b', 'if', "aren't", '5', 'once', "couldn't", '#', '"', 'doing',
            ':', '_', 'at', 'down', 'isn', 'L', ']', 'w', ' ', 'own', 'does', 'just',
            "should've", 'have', 'I', '[', 'mustn', 'J', '=', "she's", 'than', 'K',
            'mightn', 'video', 'same', 'do', 'can', 'ourselves', 'c', 'H', 'and', 'her',
            'R', 'when', 'wasn', '&', 'should', 'the', 'Y', '>', 'such', 'haven', 'O', 'M',
            'nor', "weren't", '!', 'up', 'him', 'won', 'these', '(', '-', 'shan', 'my',
            'myself', 'being', 'itself', "shouldn't", 'G', 'into', '.', '6', 'too', 'm',
            '`', "hadn't", 'e', 'g', 'over', '@', "doesn't", 'd', 'what', 'on', 'themselves',
            "wouldn't", 'not', 'some', 'q', 'been', '/', 'V', 'there', 'y', 'Z', ',', 'each',
            '$', ')', 'P', 'by', 'has', 'v', "needn't", '\\', 'of', 'now', 'was', 'out', 't',
            'aren', 'under', '4', 'hasn', 'why', 'about', "hasn't", 'didn', "haven't", "isn't",
            'l', 'F', 're', 've', 'they', "you'd", 'A', "didn't", 'E', 'yourself', 'j', '<', '~',
            "you'll", 'he', 'am', 'off', 'more', 'o', 'couldn', 'W', "mustn't", 'f', 'again',
            'against', 'p', 'with', '*', 'it', 'S', 'omitted', 'T', 'during', '%', 'doesn', 'hadn',
            "wasn't", 'had', 'you', 'r', '{', 'ain', 'having', 'were', 'C', 'how', 'his', '7', 'Q',
            "mightn't", 'very', '?', 'few', 'shouldn', 'x', 'D', '\n', "'", "don't", 'himself', 'a',
            'but', '1', "it's", 'both', 'hers', 'as', 'weren', 'further', 'in', 'll', 'yourselves',
            'while', '+', ';', 'u', 'below', 'h', '}', 'don', '\x0b', 'other', 'for', '9', '\t',
            "you've", 'all', 'i', 'after', 'until', 'then', 'is', 'z', 'ma', 'most', 'needn', 's',
            '3', '2', 'our', 'through', 'be', 'U', '|', 'N', 'where', 'between', 'theirs', 'those',
            'image omitted', 'which', 'your', 'that', '0', 'X', 'herself', 'to', 'so', 'will', 'B',
            'only', 'or', '8', 'me', 'any', 'did', '\r']



# Convert raw chat file into parsed data, returns dictionary of message data
def parse_chat(chat):
    # Create list of dicts to hold all chat info
    parsed_chat = []

    for item in chat:
        # Create a dictionary to store message data
        data = {"date": "",
                "time": "",
                "day": "",
                "author": "",
                "message": "",
                "words": "",
                "emoji": ""}

        # If the line doesn't begin with a date and doesn't begin with unicode
        # then merge the message with the previous message as it was part of that previous message
        if not regex.match(REGEX_DATE, item) and not item.startswith("\u200e"):
            parsed_chat[-1]["message"] += "\n" + item
            continue

        if not regex.search(FULL_MESSAGE, item) or regex.search(START_MESSAGE, item):
            continue

        # Create variables for the dict using regular expression search and selecting the appropriate group
        message_date = datetime.strptime(regex.search(FULL_MESSAGE, item).group(2), '%d/%m/%Y').strftime('%Y-%m-%d')
        message_time = regex.search(FULL_MESSAGE, item).group(3)
        message_author = regex.search(FULL_MESSAGE, item).group(4)
        message_message = regex.search(FULL_MESSAGE, item).group(5)
        message_day = datetime.strptime(message_date, '%Y-%m-%d').strftime('%A')
        message_words = len(message_message.split())

        # If author has multiple names, condense to first name only
        if ' ' in message_author:
            message_author = message_author.split()[0]

        # Remove unicode from message, which is always at the start of the message if missing media files
        if "\u200e" in message_message:
            message_message = message_message[1:]

        # Convert 12hr time from chat log into 24hr time
        message_time = datetime.strptime(message_time, '%I:%M:%S %p').time()
        message_time = message_time.strftime('%H:%M:%S')

        # Populate data dictionary with message data
        data["date"] = message_date
        data["day"] = message_day
        data["time"] = message_time
        data["author"] = message_author
        data["message"] = message_message
        data["words"] = message_words

        # Append data dictionary to the chat list
        parsed_chat.append(data)

    # Go back over messages and find emojis
    for m in parsed_chat:
        m["emoji"] = emoji_count(m["message"])

    return parsed_chat


# Find all emoji in message
def emoji_count(message):
    emoji_list = ''
    data = regex.findall(r'\X', message)
    for word in data:
        if any(char in emoji.UNICODE_EMOJI_ENGLISH for char in word):
            emoji_list += word + ','
    return emoji_list


# Creates list of top 20 most used emoji and their counts
def emoji_list(rows):
    # Iterate over row and create a list of lists of emojis used in messages
    emoji_list1 = []
    for item in rows:
        for x in item:
            emoji_list1.append(x.split(','))

    # Merge all lists into a mega list
    emoji_list2 = []
    for i in emoji_list1:
        emoji_list2 += i
    
    # Count the top 20 emojis into a list of tuples ('emoji','count')
    # the first tuple is empty as the Counter was adding up the empty parts from the emoji list
    counted_emoji = Counter(emoji_list2).most_common(11)
    counted_emoji[0] = ('Emoji', 'Count')
    return counted_emoji


# Create a list of tuples of the number of messages sent on ALL dates between start and end of chat
def messages_per_day(rows):
    # Clean up start and end date to be used by pandas function
    start_date = rows[0][0].replace("/", "")
    end_date = rows[-1][0].replace("/", "")

    # Create list of all dates in the YYYY/MM/DD format
    all_dates = [d.strftime('%Y-%m-%d') for d in pd.date_range(start_date, end_date)]

    # Create list of zeroes of equal length to all_dates
    date_counts = [0 for i in range(len(all_dates))]

    # Merge the above lists into a dictionary of all dates, with 0 as the value
    clean_date_dict = dict(list(zip(all_dates, date_counts)))

    # Merge the clean_date_list with the rows date dictionary so now all dates have message number data
    merged_date_dict = clean_date_dict | dict(rows)

    # Change dictionary to list of lists
    merged_date_list = list(map(list, merged_date_dict.items()))

    # Convert dict to tuples and include the header data
    tuples = [tuple(x) for x in merged_date_list]
    tuples.insert(0, ('Date', 'Messages'))

    # Return list of tuples
    return tuples


# Convert list of tuples into list of lists and insert a header
def author_count(rows):
    author_counts = [list(x) for x in rows]
    author_counts.insert(0, ['Author', 'Messages'])
    return author_counts


# Find the average reply time of a person within a given time period in seconds
def reply_time(rows, name, time):
    # List to store all times between texts
    message_gaps = []

    # Convert list of tuples into list of lists
    rows = [list(x) for x in rows]

    # Iterate through list
    for i in range(1, len(rows)):
        # Find the author's message
        if rows[i][0] == name:
            # Check if the author is replying to someone else
            if rows[i-1][0] != name:
                # Create datetime objects for the author's message and the person they are replying to
                start_datetime = datetime.strptime(str(rows[i-1][1]) + ' ' + str(rows[i-1][2]), '%Y-%m-%d %H:%M:%S').timestamp()
                end_datetime = datetime.strptime(str(rows[i][1]) + ' ' + str(rows[i][2]), '%Y-%m-%d %H:%M:%S').timestamp()
                time_delta = end_datetime - start_datetime
                # Only find time between messages based on the given time parameter
                if time_delta < time and time_delta > 0:
                    # Append time_delta to message_gap lists
                    message_gaps.append(int(time_delta))

    # Find average time_delta in seconds
    avg_time_delta = int(sum(message_gaps) / len(message_gaps))

    # Convert the seconds into H:M:S format and then return it as a string (using slices to only take the relavant time period)
    time_string = str(timedelta(seconds=avg_time_delta))
    if time_string[2] == '0':
        return time_string[3:]  
    else:
        return time_string[2:]


# Find total length of chat history
def daterange(rows):
    enddate= datetime.strptime(rows[0][0], '%Y-%m-%d')
    startdate = datetime.strptime(rows[0][1], '%Y-%m-%d')
    datedelta = str(enddate - startdate)
    return datedelta[:-13]


# Sorts the fastest replier
def fastestauthor(authorsDelta):
    newDelta = []
    for author in authorsDelta:
        time = author[1].replace(':', '')
        newDelta.append([author[0], int(time), ''])
    sorted(newDelta, key = lambda x: x[1])
    for i in range(len(newDelta)):
        for author in authorsDelta:
            if newDelta[i][0] == author[0]:
                newDelta[i][2] = author[1]
    return sorted(newDelta, key = lambda x: x[1])


# Generate wordcloud and find most common word
def wordcloudgen(rows, folder):
    # Convert tuple to single string of all messages
    rawtext = ''
    for item in rows:
        rawtext += ' ' + item[0]
    # Split words using regex
    textlist = regex.findall(r'\w+', rawtext)
    # Filter out non-words (like 'a', 'and', 'at') into a list of words, will be used to find most common word
    filtered_word_list = [w for w in textlist if w not in STOPWORDS]
    # Combine filtered words back into string to be used by wordcloud
    filtered_text = ' '.join(filtered_word_list)
    # Generate a wordcloud object
    wc = WordCloud(
        background_color = '#fff',
        stopwords = STOPWORDS,
        height=1000,
        width=1000,
        max_words=200)
    # Generate wordcloud image, save to static folder
    wc.generate(filtered_text)
    filename = folder + '/wordcloud.png'
    wc.to_file(filename)
    # Find most common words
    word_counter = {}
    for word in filtered_word_list:
        if word in word_counter:
            word_counter[word] += 1
        else:
            word_counter[word] = 1

    popular_words = sorted(word_counter, key = word_counter.get, reverse = True)

    return ', '.join(popular_words[:3]).lower()
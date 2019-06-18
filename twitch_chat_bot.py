import socket
import logging
from emoji import demojize
import re
import time
import argparse
from twitch_clipper import create_twitch_clip
import settings
from urllib import request
import json


## Miscellaneous
cycle_time = 10
msg_count = []
start_peak = None
start_chat_activity_avg = None
start_activity_threshold = 2.0
continue_activity_threshold = 1.5
messages_full_period = []
emote_feelings = [
    ("awesome", "Pog"), ("awesome", "PogU"), ("awesome", "POGGERS"), ("awesome", "PogChamp"),
    ("funny", "LULW"), ("funny", "LUL"), ("funny", "OMEGALUL"), ("funny", "DuckerZ"),
    ("sad", "PepeHands"), ("sad", "FeelsBadMan"),
    ("cringe", "haHAA"),
    ("racial", "Trihard"), ("racial", "KKona"),
    ("scary", "monkaS"), ("scary", "monkaW"),
    ("sexy", "gachi"), ("sexy", "kreyGASM")
] 
url = "https://adsai.dk/twitch-clipper/clips" 
 

def main(channel_name):
    sock = init(channel_name)

    while True:      
        messages = get_messages(cycle_time, sock)

        chat_activity_avg = update_avg(messages)
        print("Chat avg: ", chat_activity_avg)
        print("Messages len: ", len(messages))

        if chat_activity_avg is not None:
            clip_or_not(messages, chat_activity_avg, channel_name)
        
        print(" ")
   
            
            
def init(channel_name):
    server = 'irc.chat.twitch.tv'
    port = 6667
    channel = '#' + channel_name

    sock = socket.socket()
    sock.connect((server,port))
    sock.send(f"PASS {settings.token}\n".encode('utf-8'))
    sock.send(f"NICK {settings.username}\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\n".encode('utf-8'))
    return sock

# 
def get_messages(cycle_time, sock):
    curr_time = time.time()
    start_time = time.time()
    messages = []
    
    while curr_time - start_time < cycle_time:
            curr_time = time.time()

            chat_msg = scan_chat(sock)
            if chat_msg is not 0:
                messages.append(chat_msg)
                
    start_time = time.time()
    return messages

def scan_chat(sock):    
    resp = sock.recv(2048).decode('utf-8')
    if resp.startswith('PING'):
        sock.send("PONG\n".encode('utf-8'))
    
    elif len(resp) > 0:
        rgx = re.compile(r':([\S ]+)![^:]*:([\S ]*)')
        r1 = rgx.search(demojize(resp));
        return (r1.group(1), r1.group(2), time.time())
    
    return 0

def update_avg(messages):
    global msg_count
    msg_count_len = len(msg_count)
    print("msg_count_len: ", msg_count_len)
    
    if msg_count_len < 12:
        msg_count.append(len(messages))
        return None
    
    elif msg_count_len == 12:
        msg_count.pop(0)
        msg_count.append(len(messages))
        return sum(msg_count[:6]) / 6
    
def clip_or_not(messages, chat_activity_avg, channel_name):
    global start_peak
    global start_chat_activity_avg
    global messages_full_period
#     Get in here if there is a peak
    if(len(messages) > chat_activity_avg * start_activity_threshold and start_peak is None): 
#       Set start peak
        timestamp = messages[-1][2]
        print("set start_peak")       
        start_peak = timestamp
        start_chat_activity_avg = chat_activity_avg
        messages_full_period += messages
        
    elif start_peak is not None:
        end_peak = time.time()
        print("End - start peak: ", end_peak - start_peak)
        messages_full_period += messages
        
        if len(messages) < start_chat_activity_avg * continue_activity_threshold:
            if end_peak - start_peak >= 20:
                title = create_title(messages_full_period, channel_name)
                print("do selenium stuff")
                try:
                    link_date, link = create_twitch_clip(settings.username, settings.password, (end_peak - start_peak), channel_name, title)
                    post_clip(link, link_date, settings.rest_password)
                    
                except:
                    print("clip failed")
                    pass
            start_peak = None
            start_chat_activity_avg = None
            messages_full_period = []
            
                
#           Clip if peak is longer than 55 seconds  
#           Reset peaks to avoid getting into the if statement when not having peaks
        elif end_peak - start_peak >= 55:
            title = create_title(messages_full_period, channel_name)
            print("do selenium stuff LONG")
            try:
                link_date, link = create_twitch_clip(settings.username, settings.password, 60, channel_name, title)
                post_clip(link, link_date, settings.rest_password)
            except:
                print("clip failed")
                pass
            start_peak = None
            start_chat_activity_avg = None
            messages_full_period = []


def create_title(messages_list, channel_name):
    category_count, emote_count = categorize_messages(messages_full_period)
    title = channel_name 
    title += " " + sorted(category_count.items(), key=lambda x: x[1], reverse=True)[1][0]
    title += " " + str(sorted(emote_count.items(), key=lambda x: x[1], reverse=True)[0][0])

    return title

def categorize_messages(message_list):
    emote_category_count = {}
    emote_count = {}
    for msg in message_list:
        split_msg = msg[1].split(' ')
        for word in split_msg:
            word = word.strip()
            for index, emote in enumerate(emote_feelings):
                if emote[1] == word:
                    current_emote = emote_count.get(emote[1], 0)
                    emote_count[emote[1]] = current_emote + 1
                    category = emote_category_count.get(emote[0], 0)
                    emote_category_count[emote[0]] =  category + 1
                    break
                elif index == len(emote_feelings) - 1:
                    category = emote_category_count.get("Other", 0)
                    emote_category_count["Other"] = category + 1
                    current_word = emote_count.get(word, 0)
                    emote_count[word] = current_word + 1
                    
    return emote_category_count, emote_count

def post_clip(link, date, password):
    jsonObject = {"link": link,
                  "date": date,
                  "password":password
                  }

    req = request.Request(url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(jsonObject)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    print (jsondataasbytes)
    response = request.urlopen(req, jsondataasbytes) 
    print(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This program scans a channel on twitch, and creates clips if anything is clipworthy, based on twitch chat activity")
    
    # parser.add_argument("url", help="Add the url to be downloaded")
    parser.add_argument("streamer", help="Give a online streamers name to look at", default="sodapoppin")
    args = parser.parse_args()
    print("Hi, stats will be printed every ~10 seconds!")
    main(args.streamer.lower())

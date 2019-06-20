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


## Miscellaneous variables
#Length of interval in seconds to record a cycle of messages
cycle_time = 10

#List of the amount messages for each cycle
msg_count_cycles = []

#Time set when a chat peak happened
start_peak = None

#Chat activity avg. a few cycles before start_peak happens 
start_chat_activity_avg = None

#Threshold weights
start_activity_threshold = 2.0
continue_activity_threshold = 1.5

#All messages from the peak period. Used for creating a title
messages_in_peak_period = []

min_clip_length = 20
max_clip_length = 60

emotes = [
    "Pog", 
    "PogU", 
    "POGGERS", 
    "PogChamp", 
    "LULW", 
    "LUL", 
    "OMEGALUL", 
    "DuckerZ", 
    "PepeHands", 
    "FeelsBadMan", 
    "haHAA", 
    "TriHard", 
    "KKona", 
    "monkaS", 
    "monkaW", 
    "gachiGASM",
    "gacchiBASS", 
    "kreyGASM"
    ]

feelings = {
    "Pog":"awesome", 
    "PogU":"awesome", 
    "POGGERS":"awesome", 
    "PogChamp": "awesome", 
    "haHAA":"cringe", 
    "LULW":"funny", 
    "LUL":"funny", 
    "OMEGALUL":"funny", 
    "DuckerZ":"funny", 
    "TriHard":"racial", 
    "KKona":"racial", 
    "PepeHands":"sad",
    "FeelsBadMan":"sad", 
    "monkaS":"scary",
    "monkaW":"scary", 
    "gachiGASM":"sexy", 
    "gachiBASS":"sexy", 
    "kreyGASM":"sexy"
    }

url = "https://adsai.dk/twitch-clipper/clips" 
 

def main(channel_name):
    sock = init_IRC(channel_name)

    while True:      
        cur_cycle_messages = get_messages(cycle_time, sock)

        chat_activity_avg = update_avg(cur_cycle_messages)
        print("Chat avg.: ", chat_activity_avg)
        print("Amount of messages in current cycle: ", len(cur_cycle_messages))

        if chat_activity_avg is not None:
            clip_or_not(cur_cycle_messages, chat_activity_avg, channel_name)
        
        print(" ")

              
def init_IRC(channel_name):
    server = 'irc.chat.twitch.tv'
    port = 6667
    channel = '#' + channel_name

    sock = socket.socket()
    sock.connect((server,port))
    sock.send(f"PASS {settings.token}\n".encode('utf-8'))
    sock.send(f"NICK {settings.username}\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\n".encode('utf-8'))
    return sock

def get_messages(cycle_time, sock):
    curr_time = time.time()
    start_time = time.time()
    messages = []
    
    while curr_time - start_time < cycle_time:
            curr_time = time.time()

            chat_msg = scan_chat(sock)
            if chat_msg is not 0:
                messages.append(chat_msg)
                
    return messages

def scan_chat(sock):    
    resp = sock.recv(2048).decode('utf-8')

    if resp is not None:
        #Server checks if socket is active. If PONG is not returned, you will be removed from the relay
        if resp.startswith('PING'):
            sock.send("PONG\n".encode('utf-8'))
        
        elif len(resp) > 0:
            #Group 1 is username, group 2 is msg
            rgx = re.compile(r':([\S ]+)![^:]*:([\S ]*)')
            r1 = rgx.search(demojize(resp))
            return (r1.group(1), r1.group(2), time.time())
        
    return 0

def update_avg(messages):
    global msg_count_cycles
    
    cycle_amount = len(msg_count_cycles)
    print("Number of cycles: ", cycle_amount)
    
    #6 cycles is used for avg. msg. count + 2 additional cycles to avoid chat peaks to be incorporated in our avg. msg. count
    if cycle_amount < 8:
        msg_count_cycles.append(len(messages))
        return None
    
    else:
        msg_count_cycles.pop(0)
        msg_count_cycles.append(len(messages))
        selected_cycles = msg_count_cycles[:-2]
        return sum(selected_cycles) / len(selected_cycles)
    
def clip_or_not(cur_cycle_messages, chat_activity_avg, channel_name):
    global start_peak
    global start_chat_activity_avg
    global messages_in_peak_period
    global min_clip_length
    global max_clip_length
    
    #Get in here if there is a peak
    if(len(cur_cycle_messages) > chat_activity_avg * start_activity_threshold and start_peak is None): 
        
        #Set start peak. [0][2] is timestamp of the first message in the current cycle of messages 
        start_peak = cur_cycle_messages[0][2]
        start_chat_activity_avg = chat_activity_avg
        messages_in_peak_period += cur_cycle_messages
        print("Set start peak")       
        
    elif start_peak is not None:
        end_peak = time.time()
        print("Current length of clip: ", end_peak - start_peak)
        messages_in_peak_period += cur_cycle_messages
        
        #If peak ends
        if len(cur_cycle_messages) < start_chat_activity_avg * continue_activity_threshold:
        
            if end_peak - start_peak >= min_clip_length:
                title = create_title(messages_in_peak_period, channel_name)
                
                try:
                    link_date, link = create_twitch_clip(settings.username, settings.password, (end_peak - start_peak), channel_name, title)
                    post_clip(link, link_date, settings.rest_password)
                    
                except Exception as ex:
                    print("clip failed")
                    print(ex)
                    pass

            #Reset peaks to avoid getting into the if statement when not having peaks
            start_peak = None
            start_chat_activity_avg = None
            messages_in_peak_period = []
            
                
        #Clip if peak is longer than 60 seconds  
        elif end_peak - start_peak >= max_clip_length:
            title = create_title(messages_in_peak_period, channel_name)
            print("do selenium stuff LONG")
            try:
                link_date, link = create_twitch_clip(settings.username, settings.password, 60, channel_name, title)
                post_clip(link, link_date, settings.rest_password)
            except Exception as ex:
                    print("clip failed")
                    print(ex)
                    pass
            start_peak = None
            start_chat_activity_avg = None
            messages_in_peak_period = []

def create_title(messages_list, channel_name):
    feelings_count, emote_count = categorize_messages(messages_list)
    title = channel_name 
    title += " " + sorted(feelings_count.items(), key=lambda x: x[1], reverse=True)[0][0]
    title += " " + sorted(emote_count.items(), key=lambda x: x[1], reverse=True)[0][0]

    return title

def categorize_messages(message_list):
    emote_count = {}
    feeling_count = {}
    
    for msg in message_list:
        split_msg = msg[1].split(' ')

        for word in split_msg:
            word = word.strip()

            for emote in emotes:
                if emote == word:
                    emote_count[emote] = emote_count.get(emote, 0) + 1
                    break

    #Sum count of feelings for each emote
    for emote in emote_count.items():
        feeling = feelings[emote[0]]
        feeling_count[feeling] = feeling_count.get(feeling, 0) + emote[1]      

    return feeling_count, emote_count

def post_clip(link, date, password):
    jsonObject = {
        "url": link,
        "date": date,
        "password":password
        }

    req = request.Request(url)
    json_data = json.dumps(jsonObject)
    json_data_as_bytes = json_data.encode('utf-8')

    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', len(json_data_as_bytes))
    
    response = request.urlopen(req, json_data_as_bytes) 
    print(response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This program scans a channel on twitch and creates clips if anything is clipworthy based on twitch chat activity")
    parser.add_argument("streamer", help="Give an online streamer's name to look at", default="esl_csgo")
    parser.add_argument("-min", "--minimum_clip_length", type=int, help="Set minimum clip length", default=20)
    parser.add_argument("-max", "--maximum_clip_length", type=int, help="Set maximum clip length", default=60)
    args = parser.parse_args()

    min_clip_length = args.minimum_clip_length
    max_clip_length = args.maximum_clip_length
    print("Hi. stats will be printed every ~10 seconds!")
    main(args.streamer.lower())

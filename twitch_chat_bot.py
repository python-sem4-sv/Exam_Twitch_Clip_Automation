import socket
import logging
from emoji import demojize
import re
import time
import argparse

## Miscellaneous
threshold = 10
messages = []
msg_count_len = []
msg_count = []
start_peak = None
start_chat_activity_avg = None
emote_feelings_dict = [
    ("awesome", "Pog"), ("awesome", "PogU"), ("awesome", "POGGERS"), ("awesome", "PogChamp"),
    ("funny", "LULW"), ("funny", "LUL"), ("funny", "OMEGALUL"), ("funny", "DuckerZ"),
    ("sad", "PepeHands"), ("sad", "FeelsBadMan"),
    ("cringe", "haHAA"),
    ("racial", "Trihard"), ("racial", "KKona"),
    ("scary", "monkaS"), ("scary", "monkaW"),
    ("sexy", "gachi"), ("sexy", "kreyGASM")
]   

def main(channel_name):
    sock = init(channel_name)
    global messages
    global start_peak
    global start_chat_activity_avg

    while True:      
        messages = get_messages(threshold, messages, sock)

        chat_activity_avg = update_avg(messages, msg_count, msg_count_len)
        print("Chat avg: ", chat_activity_avg)
        print("Messages len: ", len(messages))

        if chat_activity_avg is not None:
            start_peak, start_chat_activity_avg = clip_or_nah(messages, chat_activity_avg, start_peak, start_chat_activity_avg)
        
        print(" ")

            
            
            
            
            
def init(channel_name):
    server = 'irc.chat.twitch.tv'
    port = 6667
    channel = '#' + channel_name
    nickname = 'pythonprojectbot2'
    token = 'oauth:masqj2izeea5xr595pjftfhfuvw2bw'

    sock = socket.socket()
    sock.connect((server,port))
    sock.send(f"PASS {token}\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\n".encode('utf-8'))
    return sock

# 
def get_messages(threshold, messages, sock):
    messages = []
    curr_time = time.time()
    start_time = time.time()
    
    while curr_time - start_time < threshold:
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

def update_avg(messages, msg_count, msg_count_len):
    msg_count_len = len(msg_count)
    print("msg_count_len: ", msg_count_len)
    
    if msg_count_len < 12:
        msg_count.append(len(messages))
        return None
    
    elif msg_count_len == 12:
        msg_count.pop(0)
        msg_count.append(len(messages))
        return sum(msg_count[:6]) / 6
    
def clip_or_nah(messages, chat_activity_avg, start_peak = None, start_chat_activity_avg = None):
#     Get in here if there is a peak
    if(len(messages) > chat_activity_avg * 2.0 and start_peak is None): 
#       Categorize what type of clip this is
        category_count, emote_count = categorize_messages(messages)
#       Set start peak
        timestamp = messages[-1][2]
        print("set start_peak")       
        return timestamp, chat_activity_avg
        
    elif start_peak is not None:
        end_peak = time.time()
        print("End - start peak: ", end_peak - start_peak)
        
        if len(messages) < start_chat_activity_avg * 1.5:
            if end_peak - start_peak >= 20:
                print("do selenium stuff")
#                 do_selenium_stuff(end_peak - start_peak)
            return None, None
            
                
#           Clip if peak is longer than 55 seconds  
#           Reset peaks to avoid getting into the if statement when not having peaks
        elif end_peak - start_peak >= 55:
            print("do selenium stuff LONG")
#             do_selenium_stuff(60)
            return None, None

    return start_peak, start_chat_activity_avg

def categorize_messages(message_list):
    emote_category_count = {}
    emote_count = {}
    for msg in message_list:
        split_msg = msg[1].split(' ')
        for word in split_msg:
            word = word.strip()
            for index, emote in enumerate(emote_feelings_dict):
                if emote[1] == word:
                    current_emote = emote_count.get(emote[1], 0)
                    emote_count[emote[1]] = current_emote + 1
                    category = emote_category_count.get(emote[0], 0)
                    emote_category_count[emote[0]] =  category + 1
                    break
                elif index == len(emote_feelings_dict) - 1:
                    category = emote_category_count.get("Other", 0)
                    emote_category_count["Other"] = category + 1
                    current_word = emote_count.get(word, 0)
                    emote_count[word] = current_word + 1
                    
    return emote_category_count, emote_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This program scans a channel on twitch, and creates clips if anything is clipworthy, based on twitch chat activity")
    
    # parser.add_argument("url", help="Add the url to be downloaded")
    parser.add_argument("-s","--streamer", help="Give a online streamers name to look at", default="sodapoppin")
    args = parser.parse_args()
    print("Hi, stats will be printed every ~10 seconds!")
    main(args.streamer)

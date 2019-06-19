import os
import time
import pickle
import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import settings

def run_chat_bot(channel, time_slow, time_fast):
    message = "Hello my dude!"
    base_url = f'https://www.twitch.tv/{channel}/chat?popout='
    driver_path = "webdrivers/chromedriver"
    browser = webdriver.Chrome(driver_path)

    browser.get(base_url)

    cookie_path = './demo_cookies.txt'
    cookie_file_exists = os.path.isfile(cookie_path)

    if cookie_file_exists:
        load_cookie(browser, cookie_path)
        browser.refresh()
    else:
        browser.implicitly_wait(10)

        chat_field = browser.find_element_by_xpath("//textarea[@data-a-target='chat-input']")
        chat_field.send_keys(message)
        chat_field.send_keys(Keys.ENTER)

        login_username_field = browser.find_element_by_xpath('/html/body/div[2]/div/div/div/div[1]/div[1]/div/form/div/div[1]/div/div[2]/input')
        login_password_field = browser.find_element_by_xpath("//input[@autocomplete='current-password']")

        login_username_field.send_keys(settings.username_demo)
        login_password_field.send_keys(settings.password_demo)

        #login_password_field.send_keys(Keys.ENTER)
        login_submit = browser.find_element_by_xpath("//button[@data-a-target='passport-login-button']")
        login_submit.click()

        #Sleep to sure that all of the cookies are saved
        time.sleep(2)
        save_cookie(browser, cookie_path)
        browser.refresh()        
    
    chat_field = browser.find_element_by_xpath("//textarea[@data-a-target='chat-input']")

    post_messages(chat_field, time_slow, time_fast)
    
    #actions = ActionChains(browser)

def save_cookie(driver, path):
    with open(path, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
    with open(path, 'rb') as cookiesfile:
        cookies = pickle.load(cookiesfile)
        for cookie in cookies:
            driver.add_cookie(cookie)


def post_messages(chat_field, time_slow, time_fast):
    while True:
        # SLow messages
        # messages = [1,2,3,4,5,6,7,8,9,10]
        slow_start_time = time.time()
        slow_delta_time = 0
        msg_nr = 0
        while time_slow >= slow_delta_time:
            #chat_field.send_keys(messages[msg_nr%len(messages)])
            chat_field.send_keys("slow message: " + str(msg_nr) + " ResidentSleeper", Keys.ENTER)
            time.sleep(1)
            msg_nr += 1
            slow_delta_time = time.time() - slow_start_time 
            print("slow posting time: ", slow_delta_time)


        fast_start_time = time.time()
        fast_delta_time = 0
        msg_nr = 0
        # Fast messages
        while time_fast >= fast_delta_time:
            #chat_field.send_keys(messages[msg_nr%len(messages)])
            chat_field.send_keys("fast message: " + str(msg_nr) + " PogChamp", Keys.ENTER)
            time.sleep(0.2)
            msg_nr += 1
            fast_delta_time = time.time() - fast_start_time
            print("fast posting time:", fast_delta_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Post chat messages in a twitch-channel')
    parser.add_argument('channel', help='Twitch channel to post messages in its chat')
    parser.add_argument('time_slow', type=int, help='How many seconds chatbot will post messages slowly')
    parser.add_argument('time_fast', type=int, help='How many seconds chatbot will post messages quickly')
    args = parser.parse_args()
    run_chat_bot(args.channel, args.time_slow, args.time_fast)
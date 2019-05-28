import os
import time
import pickle
import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime

def save_cookie(driver, path):
    with open(path, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
     with open(path, 'rb') as cookiesfile:
         cookies = pickle.load(cookiesfile)
         for cookie in cookies:
             driver.add_cookie(cookie)
            
def save_link(link, path):
    with open(path, 'a', encoding='utf8') as filehandler:
        filehandler.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " " + link + "\n")
        
def create_twitch_clip(username, password, clip_length_in_seconds, channel = 'greekgodx', clip_title="title:)", clip_link_path = './clip_links.txt', driver_path="webdrivers/chromedriver", cookie_path = './cookies.txt'):
    start_time = time.time()
    base_url = f'https://www.twitch.tv/{channel}'
    browser = webdriver.Chrome(driver_path) # or use driver = webdriver.PhantomJS() which will do the same without the overhead of a GUI. http://phantomjs.org/download.html
    browser.get(base_url)
    cookie_file_exists = os.path.isfile(cookie_path)

    #start time to calculate ad time
    
    if cookie_file_exists:
        load_cookie(browser, cookie_path)
        browser.refresh()
        try:
            accept_mature_filter = browser.find_element_by_xpath("//button[@id='mature-link']")
            accept_mature_filter.click()
            save_cookie(browser, cookie_path)
        except Exception:
            pass
    else:
        #Check if there is a mature filter and accept et, else move along
        try:
            accept_mature_filter = browser.find_element_by_xpath("//button[@id='mature-link']")
            accept_mature_filter.click()
        except Exception:
            pass
        browser.implicitly_wait(10)
        login_button = browser.find_element_by_xpath("//button[@data-a-target='login-button']")
        login_button.click()
        login_username_field = browser.find_element_by_xpath('/html/body/div[2]/div/div/div/div[1]/div/div/form/div/div[1]/div/div[2]/input')
        login_password_field = browser.find_element_by_xpath("//input[@autocomplete='current-password']")

        login_username_field.send_keys(username)
        login_password_field.send_keys(password)

        login_submit = browser.find_element_by_xpath("/html/body/div[2]/div/div/div/div[1]/div/div/form/div/div[3]/button")
        login_submit.click()
        #Sleep to sure that all of the cookies are saved
        time.sleep(2)
        save_cookie(browser, cookie_path)
    actions = ActionChains(browser)
    #Implicitly wait for potential ads
    browser.implicitly_wait(35)
    try:
        ad_player = browser.find_element_by_xpath('//*[@id="default-player"]/div/div[5]/div[2]')
    except Exception:
        pass
    #Click the clip button
    clip_button = browser.find_element_by_class_name('pl-clips-button').send_keys(Keys.ENTER)

    #end time for length of ad
    end_time = time.time()
    

    #Switch the active tab to the new tab which the button opened
    browser.switch_to.window(browser.window_handles[1])
    drag_handle_left = browser.find_element_by_xpath("//*[@id='root']/div/div/div/div[3]/div/div/main/div/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[1]")
    #the timeline of the clip
    drag_bar_width = browser.find_element_by_xpath('//*[@id="root"]/div/div/div/div[3]/div/div/main/div/div/div[3]/div/div[2]/div[1]/div').value_of_css_property('width')[0:3]
    
    #The text this returns is in the following format: "xx:xx - xx:xx"
    clip_length = browser.find_element_by_xpath('//*[@id="root"]/div/div/div/div[3]/div/div/main/div/div/div[3]/div/div[2]/div[1]/div/div/div/div[1]/div/div/div/p[2]').get_attribute("innerHTML")
    clip_length = int(clip_length[11::])
    drag_bar_width = int(drag_bar_width)/(60 + clip_length)
    
    #Move the bar all the way to the right to make the length 5 seconds, so we can set the real length of the clip consistently
    actions.click_and_hold(drag_handle_left).move_by_offset(500, 0).release().perform()
    
    #Drag the clip length bar to the left
    actions.click_and_hold(drag_handle_left).move_by_offset(-drag_bar_width * (clip_length_in_seconds - 5), 0).release().perform()
    # take ad time into consideration when making the clip
    clip_bar = browser.find_element_by_xpath('//*[@id="root"]/div/div/div/div[3]/div/div/main/div/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[2]')
    #drag entire blue clip bar, corresponding to length of ad
    actions.click_and_hold(clip_bar).move_by_offset(-drag_bar_width * (end_time - start_time), 0).release().perform()

    #add title
    title = clip_title
    title_field = browser.find_element_by_xpath("//*[@id='cmgr-title-input']")
    title_field.send_keys(title)

    #submit clip
    clip_submit = browser.find_element_by_xpath("//*[@id='root']/div/div/div/div[3]/div/div/main/div/div/div[3]/div/div[2]/div[2]/div[2]/div/div/div/button/div/div")
    clip_submit.click()

    #copy link
    clip_link = browser.find_element_by_xpath("//*[@id='root']/div/div/div/div[3]/div/div/main/div/div/div[3]/div/div[2]/div/div/div[1]/div[1]/div/input").get_attribute("value")
    #save link to .txt file
    save_link(clip_link, clip_link_path)
    print(datetime.now().strftime("%H:%M:%S"), "Video clipped!",clip_link)
    browser.quit()

    return datetime.now().strftime("%d/%m/%Y %H:%M:%S"), clip_link



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a twitch clip from the given channel')
    parser.add_argument('username', help='Your twitch username')
    parser.add_argument('password', help='Your twitch password')
    parser.add_argument('clip_length', type=int, help='Length of the clip in seconds')
    parser.add_argument('channel', help='Twitch channel to take the clip from')
    parser.add_argument('clip_title', help='Title of the clipped video')
    parser.add_argument('-clip_link_path', help='Path to save the .txt file of the clip link', default='./clip_links.txt')
    parser.add_argument('-driver_path', help='Path to the chromedriver (default path= ./webdrivers/chromedriver)', default='webdrivers/chromedriver')
    parser.add_argument('-cookie_path', help='Path where the selenium chrome driver cookies will be saved to and loaded from '  , default='./cookies.txt')
    args = parser.parse_args()
    create_twitch_clip(args.username, args.password, args.clip_length, args.channel, args.clip_title, args.clip_link_path, args.driver_path, args.cookie_path)
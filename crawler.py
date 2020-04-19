import os
import re
import sys
import time
import glob
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import configparser
import json

def initialize():
    # read config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not 'Common' in (config.sections()):
        print('no config file found or illegal format.')
        sys.exit(1)
    common = config['Common']
    # initialize parameters
    global LOGIN_URL
    global USER_ID
    global PASSWORD
    global BLACK_LIST
    global BROWSER_WAIT
    LOGIN_URL    = common.get('LOGIN_URL','')
    USER_ID      = common.get('USER_ID','')
    PASSWORD     = common.get('PASSWORD','')
    BLACK_LIST   = json.loads(common.get('BLACK_LIST',[]))
    BROWSER_WAIT = int(common.get('BROWSER_WAIT',10))

def connect_to_site():
    # Initialize path of WebDriver
    if 'nt' in os.name:
        CHROME_PATH = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe' # for Windows
    else:
        CHROME_PATH = '/usr/bin/google-chrome'  # for Linux
    # Initialize WebDriver
    options = webdriver.ChromeOptions()
    options.binary_location = CHROME_PATH
    #options.add_argument('--headless')
    options.add_argument('--window-size=1280,1024')
    prefs = {"download.default_directory" : '~'}
    options.add_experimental_option("prefs",prefs)
    options.add_argument('--igonore-certificate-errors')
    # connect to WebDriver
    global driver
    driver = webdriver.Chrome('chromedriver', options=options)
    # wait
    time.sleep(1)

def login_to_site():
    # move to login
    driver.get(LOGIN_URL)
    # driver.minimize_window()
    # input user name
    txtbox_user = driver.find_elements_by_name('f01')
    txtbox_user[0].send_keys(USER_ID)
    # input password
    txtbox_pass = driver.find_elements_by_name('f02')
    txtbox_pass[1].send_keys(PASSWORD)
    # click login button
    btn_login = driver.find_elements_by_name('fs')
    btn_login[1].click()
    # wait
    time.sleep(1)

def download_each_picture_page():
    a_tags = driver.find_elements_by_css_selector('a[href*="&number="]') # get a tags linked to picture
    for a_tag in a_tags:
        # get directory name
        dir_name = re.search('code=(.+)&',a_tag.get_attribute('href')).group(1)
        # open as new tab
        picture_url = a_tag.get_attribute('href')
        driver.execute_script('window.open()')
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(picture_url)
        WebDriverWait(driver,BROWSER_WAIT).until(lambda d: len(d.window_handles)==3)
        # download picture which img tag are linked
        img_tag = driver.find_elements_by_css_selector('img[src$=".jpg"]')
        if len(img_tag)>0:
            response = requests.get(img_tag[0].get_attribute('src'))
            os.makedirs( dir_name, exist_ok=True)
            with open( dir_name + '/' + os.path.basename(img_tag[0].get_attribute('src')), 'wb') as f:
                f.write(response.content)
        else:
            print('  couldn\'t find img tag following a tag.')
        # close tab
        driver.close()
        WebDriverWait(driver,BROWSER_WAIT).until(lambda d: len(d.window_handles)==2)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(1)
        
def loop_each_person():
    while True:
        # download all of the page
        download_each_picture_page()
        # move to next page
        img_tags = driver.find_elements_by_css_selector('a[href*="page="] > img')
        if len(img_tags)==0:     # there is no link in the case of one page.
            driver.close()
            WebDriverWait(driver,BROWSER_WAIT).until(lambda d: len(d.window_handles)==1)
            driver.switch_to.window(driver.window_handles[-1])
            break
        a_tag = img_tags[-1].find_element_by_xpath('..')
        if re.search('[0-9]+$',driver.current_url) == None or ( int(re.search('[0-9]+$',a_tag.get_attribute('href')).group(0)) >= int(re.search('[0-9]+$',driver.current_url).group(0)) ):
            next_url = a_tag.get_attribute('href')
            a_tag.click()
            WebDriverWait(driver,BROWSER_WAIT).until(lambda d: d.current_url==next_url)
            driver.switch_to.window(driver.window_handles[-1])
        else:
            driver.close()
            WebDriverWait(driver,BROWSER_WAIT).until(lambda d: len(d.window_handles)==1)
            driver.switch_to.window(driver.window_handles[-1])
            break

def download_video( response, a_tag):
    # get a tag of related picuture
    td_num = len(a_tag.find_elements_by_xpath('parent::td/preceding-sibling::td')) + len(a_tag.find_elements_by_xpath('parent::td/following-sibling::td'))
    if td_num != 4: # check not in notification cells
        print('  video discarded because existing notification cells.')
        return
    td_pos = len(a_tag.find_elements_by_xpath('parent::td/preceding-sibling::td'))   # get position in tr tags
    pic_a_tags = a_tag.find_elements_by_xpath('ancestor::tr/preceding-sibling::tr[position()=1]/child::td[position()={}]/child::a[contains(@href,\'view_type=sp\')=false()]'.format(td_pos+1))
    pic_a_tag = pic_a_tags[0]
    # generate directory and file name
    directory_name = re.search('code=(.+)$', pic_a_tag.get_attribute('href')).group(1)
    file_name = os.path.basename(response.headers['Location'])
    # save to file
    if not os.path.exists(directory_name+'/'+file_name):
        # get session from WebDriver
        headers = { 'UserAgent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}
        cookies = { cookie['name']:cookie['value'] for cookie in driver.get_cookies()}
        # download
        response = requests.get(a_tag.get_attribute('href'), headers=headers, cookies=cookies, allow_redirects=True)
        # save to file
        os.makedirs( directory_name, exist_ok=True)
        with open( directory_name+'/'+file_name, 'wb') as f:
            f.write(response.content)
            print('  video saved path={}'.format(directory_name+'/'+file_name))
    else:
        print('  video already downloaded, passed.')

def loop_each_page():
    a_tags = driver.find_elements_by_css_selector('a[href*="/service/contents.php?code="]')
    for i,a_tag in enumerate(a_tags):
        print('Index={}/{} Link={} '.format(i,len(a_tags),a_tag.get_attribute('href')))
        if 'view_type=sp' in a_tag.get_attribute('href'):
            print('  sp page, passed.')
            continue
        # get session from WebDriver
        headers = { 'UserAgent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}
        cookies = { cookie['name']:cookie['value'] for cookie in driver.get_cookies()}
        # check redirect
        response = requests.get(a_tag.get_attribute('href'), headers=headers, cookies=cookies, allow_redirects=False)
        # branch action depend on types
        if response.status_code==200:
            # case of pictures
            # check already downloaded
            if os.path.exists(re.search('code=(.+)$', a_tag.get_attribute('href')).group(1)):
                # get number of pictures
                font_tags = a_tag.find_elements_by_xpath('following-sibling::font')
                if len(font_tags)==1 and re.search('\\(([0-9]+)枚\\)', font_tags[0].text)!=None:
                    # case of being able to get number of pictures
                    files = glob.glob( re.search('code=(.+)$$', a_tag.get_attribute('href')).group(1) + '/*.jpg')
                    if re.search('code=(.+)$',a_tag.get_attribute('href')).group(1) in BLACK_LIST:
                        print('  in BLACK LIST however directory existing, passed.')
                        continue
                    if len(files) != int(re.search('\\(([0-9]+)枚\\)', font_tags[0].text).group(1)):
                        print('  some files weren\'t downloaded. on web={} existing={}'.format( int(re.search('\\(([0-9]+)枚\\)', font_tags[0].text).group(1)),len(files)))
                        a_tag.click()
                        WebDriverWait(driver,BROWSER_WAIT).until(lambda d: len(d.window_handles)==2)
                        driver.switch_to.window(driver.window_handles[-1])
                        loop_each_person()
                    else:
                        # case of uncertain
                        print( '  pictures already downloaded, passed index={} name={}'.format( i, re.search('code=(.+)$', a_tag.get_attribute('href')).group(1)))
                        continue
                else:
                    # case of uncertain because of existing what's new
                    print( '  couldn\'t confirm already downloaded, passed index={} name={}'.format( i, re.search('code=(.+)$', a_tag.get_attribute('href')).group(1)))
                    continue
            else:
                print( '  pictures will be download name={}'.format( re.search('code=(.+)$', a_tag.get_attribute('href')).group(1)))
                a_tag.click()
                WebDriverWait(driver,BROWSER_WAIT).until(lambda d: len(d.window_handles)==2)
                driver.switch_to.window(driver.window_handles[-1])
                loop_each_person()
        elif response.status_code==302 and re.search('\\.mp4$',response.headers['Location'])!=None:
            # case of video
            download_video( response, a_tag)
        else:
            print('  link of a-tag is something wrong, passed.')

def loop_top_page():
    while True:
        loop_each_page()
        a_tags = driver.find_elements_by_css_selector('a[href*="/service/index.php?page="]')
        if len(a_tags)==0:
            break;
        for a_tag in a_tags:
            if re.search( 'index\\.php\\?page=([0-9]+)#list',driver.current_url)==None: 
                current = 1
            else:
                current = val(re.search( 'index\\.php\\?page=([0-9]+)#list',driver.current_url))
            if re.search( 'index\\.php\\?page=([0-9]+)#list',a_tag.get_attribute('href'))==None: 
                next = 1
            else:
                next = int(re.search( 'index\\.php\\?page=([0-9]+)#list',a_tag.get_attribute('href')).group(1))
            print('Found new page next={} current={}'.format(next,current))
            if next > current:
                a_tag.click()
                WebDriverWait(driver,BROWSER_WAIT).until(lambda d: len(d.window_handles)==1)
                driver.switch_to.window(driver.window_handles[-1])
                break


def settlement():
    driver.quit()

initialize()
connect_to_site()
login_to_site()
loop_top_page()
settlement()
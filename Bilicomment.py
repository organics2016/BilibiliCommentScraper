import traceback

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pickle
import time
import os
import csv
import re
import json
import sys
import tempfile
import shutil

file_encoding = 'utf8'


def write_error_log(message):
    with open("video_errorlist.txt", "a", encoding=file_encoding) as file:
        file.write(message + "\n")


# def load_cookies(driver, cookies_file):
#     if os.path.exists(cookies_file):
#         with open(cookies_file, 'rb') as f:
#             cookies = pickle.load(f)
#         for cookie in cookies:
#             driver.add_cookie(cookie)
#         return True
#     return False


def load_cookies(cookies_file):
    if os.path.exists(cookies_file):
        with open(cookies_file, 'rb') as f:
            return pickle.load(f)
    return None


def manual_login(driver, cookies_file):
    input("请登录，登录成功跳转后，按回车键继续...")
    with open(cookies_file, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print("程序正在继续运行")


def scroll_to_bottom(driver):
    SCROLL_PAUSE_TIME = 4
    # B站每向下滚动一次，会加载20个一级评论。
    # 滚动次数过多，加载的数据过大，网页可能会因内存占用过大而崩溃。
    # 这里设置滚动次数为45次，最多收集到920条一级评论
    # 视频评论数 = 一级评论数 + 二级评论数，且存在虚标情况。经测试，滚动次数设为45次时，已完整爬取标称评论数为7443条的视频评论，共爬取到3581条评论。
    MAX_SCROLL_COUNT = 1
    scroll_count = 0

    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
    except NoSuchWindowException:
        print("浏览器意外关闭...")
        raise

    while scroll_count < MAX_SCROLL_COUNT:
        try:
            driver.execute_script('javascript:void(0);')
        except Exception as e:
            print(f"检测页面状态时出错，尝试重新加载: {e}")
            driver.refresh()
            time.sleep(5)
            scroll_to_bottom(driver)
            time.sleep(SCROLL_PAUSE_TIME)
            raise

        try:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        except NoSuchWindowException:
            print("关闭小窗时，浏览器意外关闭...")
            raise

        time.sleep(SCROLL_PAUSE_TIME)
        try:
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
        except NoSuchWindowException:
            print("页面向下滚动时，浏览器意外关闭...")
            raise

        if new_height == last_height:
            break

        last_height = new_height
        scroll_count += 1
        print(f'下滑滚动第{scroll_count}次 / 最大滚动{MAX_SCROLL_COUNT}次')


def write_to_csv(video_id, index, parent_idx, nickname, user_id, content, time, likes):
    file_exists = os.path.isfile(f'{video_id}.csv')

    with open(f'{video_id}.csv', mode='a', encoding=file_encoding, newline='') as csvfile:
        fieldnames = ['评论ID', '父评论ID', '用户昵称', '用户ID', '评论内容', '发布时间', '点赞数']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            '评论ID': index,
            '父评论ID': parent_idx,
            '用户昵称': nickname,
            '用户ID': user_id,
            '评论内容': content,
            '发布时间': time,
            '点赞数': likes,
        })


def main():
    # 代码文件所在的文件夹内创建一个新的文件夹，作为缓存目录。如果想自行设定目录，请修改下面代码
    current_folder = os.path.abspath('temp')
    # 首次登录获取cookie文件
    cookies_file = 'cookies.pkl'
    print("测试cookies文件是否已获取。若无，请在弹出的窗口中登录b站账号，登录完成后，窗口将关闭；若有，窗口会立即关闭")
    cookies = load_cookies(cookies_file)
    if cookies is None:
        driver = webdriver.Chrome(service=Service(executable_path=ChromeDriverManager().install()))
        driver.get('https://bilibili.com/')
        manual_login(driver, cookies_file)
        driver.quit()

    # 设置Chrome浏览器参数
    chrome_options = Options()
    # # 将Chrome的缓存目录设置为刚刚创建的临时目录
    print(current_folder)
    chrome_options.add_argument(f'--user-data-dir={current_folder}')
    chrome_options.add_argument('--disable-plugins-discovery')
    chrome_options.add_argument('--mute-audio')
    # 开启无头模式，禁用视频、音频、图片加载，开启无痕模式，减少内存占用
    # chrome_options.add_argument('--headless')  # 开启无头模式以节省内存占用，较低版本的浏览器可能不支持这一功能
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_argument("--incognito")
    # 禁用GPU加速，避免浏览器崩溃
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(executable_path=ChromeDriverManager().install()), options=chrome_options)
    driver.get('https://bilibili.com/')

    cookies = load_cookies(cookies_file)
    assert cookies is not None
    for cookie in cookies:
        driver.add_cookie(cookie)

    if os.path.exists("progress.txt"):
        with open("progress.txt", "r", encoding=file_encoding) as f:
            progress = json.load(f)
    else:
        progress = {"finished": []}

    with open('video_list.txt', 'r', encoding=file_encoding) as f:
        video_urls = f.read().splitlines()

    diffs = set(video_urls) - set(progress["finished"])

    for url in diffs:
        try:
            video_id_search = re.search(r'https://www\.bilibili\.com/video/([^/?]+)', url)
            if video_id_search:
                video_id = video_id_search.group(1)
                print(
                    f'开始爬取{video_id}：先会不断向下滚动至页面最底部，以加载全部页面。对于超大评论量的视频，这一步会相当花时间，请耐心等待')

            driver.get(url)

            # 在爬取评论之前滚动到页面底部
            scroll_to_bottom(driver)

            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "bili-comments")))
            contents = driver.find_element(By.TAG_NAME, 'bili-comments').shadow_root
            driver.implicitly_wait(10)
            feed = contents.find_element(By.ID, 'feed')
            bctr = feed.find_elements(By.TAG_NAME, 'bili-comment-thread-renderer')

            for i, reply_item in enumerate(bctr):

                comment = reply_item.shadow_root.find_element(By.ID, 'comment').shadow_root

                header = comment.find_element(By.ID, 'header')
                userinfo = header.find_elements(By.TAG_NAME, '*')[0].shadow_root
                userid = userinfo.find_element(By.ID, 'user-name').get_attribute('data-user-profile-id')
                nickname = userinfo.find_element(By.ID, 'user-name').find_element(By.TAG_NAME, 'a').text

                content = comment.find_element(By.ID, 'content')
                ccc = (content.find_elements(By.TAG_NAME, '*')[0]
                       .shadow_root.find_element(By.ID, 'contents')
                       .find_element(By.TAG_NAME, 'span').text)

                footer = comment.find_element(By.ID, 'footer')
                comment_action = footer.find_elements(By.TAG_NAME, '*')[0].shadow_root
                pubdate = comment_action.find_element(By.ID, 'pubdate').text
                likes = comment_action.find_element(By.ID, 'like').find_element(By.TAG_NAME, 'span').text

                write_to_csv(video_id,
                             index=i,
                             parent_idx=None,
                             nickname=nickname,
                             user_id=userid,
                             content=ccc,
                             time=pubdate,
                             likes=likes)
                print(f'视频{video_id}第{i}个一级评论已写入csv。正在查看这个一级评论有没有二级评论')

                # driver.execute_script("arguments[0].scrollIntoView();", reply_item)
                # time.sleep(2)
                replies = reply_item.shadow_root.find_element(By.ID, 'replies')
                replies = replies.find_elements(By.TAG_NAME, '*')[0].shadow_root
                replies = replies.find_element(By.ID, 'expander-contents')
                replies = replies.find_elements(By.TAG_NAME, 'bili-comment-reply-renderer')

                for j, reply in enumerate(replies):
                    reply = reply.shadow_root

                    main = reply.find_element(By.ID, 'main')
                    userinfo = main.find_elements(By.TAG_NAME, '*')[0].shadow_root
                    userid = userinfo.find_element(By.ID, 'user-name').get_attribute('data-user-profile-id')
                    nickname = userinfo.find_element(By.ID, 'user-name').find_element(By.TAG_NAME, 'a').text

                    reply_comment = main.find_element(By.TAG_NAME, 'bili-rich-text').shadow_root
                    reply_comment = reply_comment.find_element(By.ID, 'contents')
                    reply_comment = reply_comment.find_element(By.TAG_NAME, 'span').text

                    footer = reply.find_element(By.ID, 'footer')
                    comment_action = footer.find_elements(By.TAG_NAME, '*')[0].shadow_root
                    pubdate = comment_action.find_element(By.ID, 'pubdate').text
                    likes = comment_action.find_element(By.ID, 'like').find_element(By.TAG_NAME, 'span').text

                    write_to_csv(video_id, j, i, nickname, userid, reply_comment, pubdate, likes)
                    print(f'视频{video_id}第{j}个二级评论已写入csv')

            progress["finished"].append(url)
        except:
            traceback.print_exc()
        finally:
            driver.close()


if __name__ == "__main__":
    main()

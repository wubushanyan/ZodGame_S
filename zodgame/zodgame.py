# encoding=utf8
import os
import io
import re
import sys
import platform
import subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import requests

def send_telegram_message(bot_token, chat_id, message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}'
    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        print('Telegram消息推送成功！')
    else:
        print('Telegram消息推送失败！')

def zodgame_checkin(driver, formhash):
    checkin_url = "https://zodgame.xyz/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=0"    
    checkin_query = """
        (function (){
        var request = new XMLHttpRequest();
        var fd = new FormData();
        fd.append("formhash","%s");
        fd.append("qdxq","kx");
        request.open("POST","%s",false);
        request.withCredentials=true;
        request.send(fd);
        return request;
        })();
        """ % (formhash, checkin_url)
    checkin_query = checkin_query.replace("\n", "")
    driver.set_script_timeout(240)
    resp = driver.execute_script("return " + checkin_query)
    match = re.search('<div class="c">\n(.*?)</div>\n', resp["response"], re.S)
    message = match[1] if match is not None else "签到失败"
    print(f"【签到】{message}")
    return "恭喜你签到成功!" in message or "您今日已经签到，请明天再来" in message

def zodgame_task(driver, formhash):

    def clear_handles(driver, main_handle):
        handles = driver.window_handles[:]
        for handle in handles:
            if handle != main_handle:
                driver.switch_to.window(handle)
                driver.close()
        driver.switch_to.window(main_handle)
      
    def show_task_reward(driver):
        driver.get("https://zodgame.xyz/plugin.php?id=jnbux")
        try:
            WebDriverWait(driver, 240).until(
                lambda x: x.title != "Just a moment..."
            )
            reward = driver.find_element(By.XPATH, '//li[contains(text(), "点币: ")]').get_attribute("textContent")[:-2]
            print(f"【Log】{reward}")
        except:
            pass

    driver.get("https://zodgame.xyz/plugin.php?id=jnbux")
    WebDriverWait(driver, 240).until(
        lambda x: x.title != "Just a moment..."
    )

    join_bux = driver.find_elements(By.XPATH, '//font[text()="开始参与任务"]')
    if len(join_bux) != 0 :    
        driver.get(f"https://zodgame.xyz/plugin.php?id=jnbux:jnbux&do=join&formhash={formhash}")
        WebDriverWait(driver, 240).until(
            lambda x: x.title != "Just a moment..."
        )
        driver.get("https://zodgame.xyz/plugin.php?id=jnbux")
        WebDriverWait(driver, 240).until(
            lambda x: x.title != "Just a moment..."
        )

    join_task_a = driver.find_elements(By.XPATH, '//a[text()="参与任务"]')
    success = True

    if len(join_task_a) == 0:
        print("【任务】所有任务均已完成。")
        return success
    handle = driver.current_window_handle
    for idx, a in enumerate(join_task_a):
        on_click = a.get_attribute("onclick")
        try:
            function = re.search("""openNewWindow(.*?)\(\)""", on_click, re.S)[0]
            script = driver.find_element(By.XPATH, f'//script[contains(text(), "{function}")]').get_attribute("text")
            task_url = re.search("""window.open\("(.*)", "newwindow"\)""", script, re.S)[1]
            driver.execute_script(f"""window.open("https://zodgame.xyz/{task_url}")""")
            driver.switch_to.window(driver.window_handles[-1])
            try:
                WebDriverWait(driver, 240).until(
                    lambda x: x.find_elements(By.XPATH, '//div[text()="成功！"]')
                )
            except:
                print(f"【Log】任务 {idx+1} 广告页检查失败。")
                pass

            try:     
                check_url = re.search("""showWindow\('check', '(.*)'\);""", on_click, re.S)[1]
                driver.get(f"https://zodgame.xyz/{check_url}")
                WebDriverWait(driver, 240).until(
                    lambda x: len(x.find_elements(By.XPATH, '//p[contains(text(), "检查成功, 积分已经加入您的帐户中")]')) != 0 
                        or x.title == "BUX广告点击赚积分 - ZodGame论坛 - Powered by Discuz!"
                )
            except:
                print(f"【Log】任务 {idx+1} 确认页检查失败。")
                pass

            print(f"【任务】任务 {idx+1} 成功。")
        except Exception as e:
            success = False
            print(f"【任务】任务 {idx+1} 失败。", type(e))
        finally:
            clear_handles(driver, handle)
    
    show_task_reward(driver)

    return success

def zodgame(cookie_string):
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--headless")
    driver = uc.Chrome(driver_executable_path = """C:\SeleniumWebDrivers\ChromeDriver\chromedriver.exe""",
                       browser_executable_path = """C:\Program Files\Google\Chrome\Application\chrome.exe""",
                       options = options)

    # Load cookie
    driver.get("https://zodgame.xyz/")

    if cookie_string.startswith("cookie:"):
        cookie_string = cookie_string[len("cookie:"):]
    cookie_string = cookie_string.replace("/","%2")
    cookie_dict = [ 
        {"name" : x.split('=')[0].strip(), "value": x.split('=')[1].strip()} 
        for x in cookie_string.split(';')
    ]

    driver.delete_all_cookies()
    for cookie in cookie_dict:
        if cookie["name"] in ["qhMq_2132_saltkey", "qhMq_2132_auth"]:
            driver.add_cookie({
                "domain": "zodgame.xyz",
                "name": cookie["name"],
                "value": cookie["value"],
                "path": "/",
            })
    
    driver.get("https://zodgame.xyz/")
    
    WebDriverWait(driver, 240).until(
        lambda x: x.title != "Just a moment..."
    )
    assert len(driver.find_elements(By.XPATH, '//a[text()="用户名"]')) == 0, "Login fails. Please check your cookie."
        
    formhash = driver.find_element(By.XPATH, '//input[@name="formhash"]').get_attribute('value')
    assert zodgame_checkin(driver, formhash) and zodgame_task(driver, formhash), "Checkin failed or task failed."

    driver.close()
    driver.quit()

def get_info(cookie_string,result_string):
    sign_in_info_url = "https://zodgame.xyz/plugin.php?id=dsu_paulsign:sign"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/119.0.0.0 Safari/537.36",
        "Cookie": cookie_string,
        "Referer": "https://zodgame.xyz/plugin.php?id=dsu_paulsign:sign",
        "Sec-Ch-Ua-Platform": "Windows",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Site": "same-origin"
    }
    response = requests.get(sign_in_info_url, headers=headers)
    if "今天已经签到过了" in response.text:
        # print("成功获取签到信息")
        pattern = re.compile(   r'<p><font color=.*?><b>(.*?)</b></font> , 您累计已签到: <b>(\d+)</b> 天</p>'
                                r'[\s\S]*?'
                                r'<p>您本月已累计签到:<b>(\d+)</b> 天</p>'
                                r'[\s\S]*?'
                                r'<p>您上次签到时间:<font color=".*?">(.*?)</font> </p>'
                                r'[\s\S]*?'
                                r'<p>您目前获得的总奖励为:酱油 <font color=".*?"><b>(\d+)</b></font> 瓶 , 上次获得的奖励为:酱油 <font color=".*?"><b>(\d+)</b></font> 瓶.</p>'
                                r'[\s\S]*?'
                                r'<p>您目前的等级: <font color=".*?"><b>(.*?)</b></font> , Tips: 您只需再签到 <font color=".*?"><b>(\d+)</b></font> 天就可以提升到下一个等级: <font color=".*?"><b>(.*?)</b></font> .</p>',
                                re.DOTALL)

        matches = pattern.search(response.text)

        if matches:
            nickname = matches.group(1)
            accumulated_days = matches.group(2)
            monthly_days = matches.group(3)
            last_sign_in_time = matches.group(4)
            total_rewards = matches.group(5)
            last_rewards = matches.group(6)
            current_level = matches.group(7)
            days_to_next_level = matches.group(8)
            next_level = matches.group(9)

            result_string = (   f"===ZODGAME签到信息===\n"
                                f"昵称: {nickname}\n"
                                f"累计签到天数: {accumulated_days}\n"
                                f"本月签到天数: {monthly_days}\n"
                                f"上次签到时间: {last_sign_in_time}\n"
                                f"总奖励: {total_rewards}\n"
                                f"上次奖励: {last_rewards}\n"
                                f"当前等级: {current_level}\n"
                                f"距离下一等级还需签到天数: {days_to_next_level}\n"
                                f"下一等级: {next_level}"
                            )
            # print(result_string)
        else:
            result_string = "未找到匹配的信息"
            print("未找到匹配的信息")

if __name__ == "__main__":
    TG_BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
    TG_CHAT_ID = os.environ["TG_CHAT_ID"]
    # ZODGAME_COOKIE = os.environ["ZODGAME_COOKIE"]
    cookie_string = sys.argv[1]
    result_string=""
    assert cookie_string
    
    zodgame(cookie_string)
    get_info(cookie_string,result_string)
    send_telegram_message(TG_BOT_TOKEN, TG_CHAT_ID, result_string)

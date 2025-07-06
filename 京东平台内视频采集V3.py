import asyncio
from playwright.async_api import async_playwright
import os
import re
import time
import json
import random
import datetime
import urllib.parse
import requests
import urllib.request
import PySimpleGUI as sg
import threading


start_id="467819200"
end_id = "467820000"
big_dir="D:/京东采集融化视频"
br_PORT="12345" #浏览器端口

folder_path_cwd = os.getcwd()
# 配置文件 固定的
config_TMP = 'config_JD_DownVideo.json'
# 保存配置文件 
def saveConf(start_id,end_id,big_dir):
    dataConfig = { 'start_id': start_id, 'end_id': end_id, 'save_dir': big_dir}
    with open(f'{folder_path_cwd}/{config_TMP}', 'w',encoding='utf-8') as file_object:json.dump(dataConfig, file_object)   

#  初始化 读取配置文件 初始化
if not os.path.exists(f'{folder_path_cwd}/{config_TMP}'):
    saveConf(start_id,end_id,big_dir) # TagCNameL1 TagCNameL2   
else: 
    with open(f'{folder_path_cwd}/{config_TMP}', 'r',encoding='utf-8') as f: 
        data = json.load(f) 
        
        start_id = data['start_id'] 
        end_id = data['end_id'] 
        big_dir = data['save_dir'] 


today_date = datetime.datetime.today().strftime("%Y-%m-%d")# 获取今天的日期 


#取txt行，返回行列表 广告语句，从广告配置文件 中， 一行一个， 随机一个
def read_txt_file(txt_file):
    lines = []
    try:
        with open(txt_file, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"File '{txt_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")    
    return lines


#保存发布日志记录 到本地txt文件 中, id,title , 日志信息
async def saveLog(ID,Title,logMSG):     
    today_date = datetime.datetime.today().strftime("%Y-%m-%d")# 获取今天的日期 
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file_path = f"downLog_{today_date}.txt"
    with open(log_file_path, "a", encoding="utf-8") as file:
        file.write(current_time+","+str(ID) + "," + Title + "," + logMSG+ "\n")

 

async def get_video_info(page, url):
    await page.goto(url)
    await page.wait_for_selector('.mainvideo-postercon-img')
    await page.waitForSelector('.mainvideo-video')
    await page.waitForSelector('.desc-videotitle')
    await page.click('.desc-videotitle')
    await page.waitForNavigation()
    redirect_url = page.url
    if 'https://cfe.m.jd.com/' in redirect_url:
        sg.popup('Please solve the security verification manually and click OK to continue')
        await page.waitForNavigation()
        redirect_url = page.url
    if 'https://item.m.jd.com/product/' in redirect_url:
        skuid = re.findall(r'https://item.m.jd.com/product/(\d+).html', redirect_url)[0]
        video_title = await page.innerText('.desc-videotitle')
        video_url = await page.getAttribute('.mainvideo-video', 'src')
        video_cover_url = await page.getAttribute('.mainvideo-postercon-img', 'src')
        return skuid, video_title, video_url, video_cover_url
    else:
        return None

async def download_video(skuid, video_title, video_url, video_cover_url, save_dir):
    # 构造本地视频路径和文件名 
    #video_title 视频文件名中不能含有|#;$%@'()<>+\字符 + ,
    # 定义非法字符的正则表达式
    illegal_chars_regex = r'[|#/:.!"?*,;$%@\'()<>+~\\]' # |#;$%@'()<>+\   :.!"?* 
    # 替换非法字符为空字符串
    sanitized_video_title = re.sub(illegal_chars_regex, '', video_title)
    sanitized_video_title =sanitized_video_title.replace(",","，").replace("!"," ")
    video_name = skuid + ' ' + sanitized_video_title + '.mp4'
    video_path = os.path.join(save_dir, video_name)
    # 获取视频
    video_content = requests.get(video_url).content
    # 打开本地视频文件并写入内容
    with open(video_path, 'wb') as f:
        f.write(video_content)        
    print(f'视频已下载至:{video_path}')
    

# 图片下载 备用 ， 可能以后手机版会用到，暂时不用
async def download_img(skuid, video_title, video_url, video_cover_url, save_dir):
    # 获取图片    
    # 构造本地图片路径和文件名
    cover_name = skuid + ' ' + video_title + '.jpg'
    cover_path = os.path.join(save_dir, cover_name)   

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    # urllib.request.urlretrieve(video_cover_url, save_dir)
    urllib.request.urlretrieve(video_cover_url, cover_path)         
    print(f'封图已下载至:{cover_path}')



async def main(start_id, end_id, save_dir):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f'http://localhost:{br_PORT}/')
        contexts = browser.contexts     
        context = contexts[0] # 改多UA 2024.09.28====== ,新注消 原生效的


        # 定义多个不同的 User-Agent  randN = random.randint(9, 30)
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.*RAND10-30* (KHTML, like Gecko) Chrome/94.*RAND1-9*.4606.*RAND30-60* Safari/537.*RAND10-30*',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.*RAND10-30*; rv:*RAND30-60*.0) Gecko/2010010*RAND1-9* Firefox/*RAND30-60*.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.*RAND10-30* (KHTML, like Gecko) Version/*RAND10-30*.0 Mobile/15E1*RAND30-60* Safari/604.*RAND1-9*',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.*RAND30-60* (KHTML, like Gecko) Chrome/94.0.46*RAND10-30*.6*RAND1-9* Safari/537.*RAND30-60* OPR/78.*RAND1-9*.4093.23*RAND1-9*',
            # 'Mozilla/5.0 (Windows NT 10.3; Win64; x64) AppleWebKit/535.33 (KHTML, like Gecko) Chrome/62.0.5322.112 Safari/576.2',
            # 'Mozilla/5.0 (Windows NT 10.4; Win64; x64) AppleWebKit/547.34 (KHTML, like Gecko) Chrome/63.0.4134.154 Safari/551.4',
            # 'Mozilla/5.0 (Windows NT 10.5; Win64; x64) AppleWebKit/536.35 (KHTML, like Gecko) Chrome/64.0.1145.145 Safari/506.5',
            # 'Mozilla/5.0 (Windows NT 10.6; Win64; x64) AppleWebKit/503.36 (KHTML, like Gecko) Chrome/66.0.2162.136 Safari/523.6',
            # 'Mozilla/4.0 (Windows NT 10.7; Win64; x64) AppleWebKit/507.37 (KHTML, like Gecko) Chrome/67.0.2173.117 Safari/546.7',
            # 'Mozilla/3.0 (Windows NT 10.8; Win64; x64) AppleWebKit/508.38 (KHTML, like Gecko) Chrome/68.0.2148.128 Safari/515.8',
            # 添加更多 User-Agent
        ]
        
        # print(type(page))
        # page = await context.new_page()
        for i in range(start_id, end_id+1):

            # page.close()    # 改多UA 2024.09.28====== 新加
            if i % 10 == 0:  # 每隔10个值执行以下操作
                rand1=random.randint(1, 9)
                # rand10=random.randint(10, 30)
                # rand30=random.randint(30, 60)

                # # await context.close() # 改多UA 2024.09.28====== 新加
                # user_agent_MB = random.choice(user_agents) #模板
                # user_agent=user_agent_MB.replace("*RAND1-9*",str(rand1)).replace("*RAND10-30*",str(rand10)).replace("*RAND30-60*",str(rand30))
                # context = await browser.new_context(user_agent=user_agent) #加新context后 会丢失登录信息
                time.sleep(rand1)

            page = await context.new_page() # 改多UA 2024.09.28====== ， 原来在for 循环外

            url = f'https://h5.m.jd.com/active/faxian/video/index.html?id={i}'
            #       https://h5.m.jd.com/active/faxian/video/index.html?id=467819146
            await page.goto(url)
            print("等待页面加载完成...")
            await page.wait_for_load_state("load")  # 等待页面完全加载完成 
            # await page.wait_for_timeout(3000)
            print("页面加载完成，执行后续操作")
            
            time.sleep(3)
            hasVideo=False
            try:
                # 等待视频元素出现 #root > div > div.index-top > div.mainvideo
                video_element = await page.query_selector('#root > div > div.index-top > div.mainvideo')
                await page.wait_for_selector('#root > div > div.index-top > div.mainvideo', timeout=6000)                
                if video_element:                    
                    print(f"{i}: YES1 有 主视频元素")                
                    # 检查是否有商品元素 #root > div > div.index-top > div.index-info > div.index-desc-shoppingbag > div.shopingbag > div > div                    
                    shopping_bag_element = await page.query_selector('#root > div > div.index-top > div.index-info > div.index-desc-shoppingbag > div.shopingbag > div.shopingbag-single')
                    #root > div > div.index-top > div.index-info > div.index-desc-shoppingbag > div.shopingbag > div > div
                    #root > div > div.index-top > div.index-info > div.index-desc-shoppingbag > div.shopingbag > div.shopingbag-single
                    #加一个只选单个商品的视频 多商品的过滤掉，暂时不要， 以后再修改为多商品的取第一个商品                    
                    if shopping_bag_element:
                        hasVideo = True
                        print(f"{i}: YES2 +1有 购物车元素")
                    else:
                        hasVideo = False
                        print(f"{i}: NO 层2 无 购物车元素")
                        await page.close() # 改多UA 2024.09.28====== 新加
                        # continue
                else:
                    hasVideo = False
                    print(f"{i}: NO 层1 无 主视频元素")  
                    await page.close() 


            except:
                hasVideo = False  
                print(f"{i}: nono except 无 主视频元素 ") 
                await page.close() # 改多UA 2024.09.28====== 新加 
                # continue

            if hasVideo:
                # page.wait_for_selector()
                # video_info = await get_video_info(page, url)
                ##posterId
                try:
                    await page.wait_for_selector('img.mainvideo-postercon-img',timeout=9000)
                    # print("已发现识别到 视频封面图元素 ")
                except:
                    await page.close() # 改多UA 2024.09.28====== 新加
                    continue    

                video_title = await page.inner_text('span.desc-videotitle') 
                #视频标题 #root > div > div.index-top > div.index-info > div.index-desc-shoppingbag > div.desc > span.desc-videotitle
                video_url = await page.get_attribute('video.mainvideo-video', 'src') #视频地址 #root > div > div.index-top > div.mainvideo > video
                #https://jvod.300hu.com/vod/product/60be922e-4f2b-424c-a5b6-25a6cd902b66/0198697ff65d4f8a84aa891e0d2edb8f.mp4?info=82238-3000773-h264-aac
                cover_url = await page.get_attribute('img.mainvideo-postercon-img', 'src') #封面图地址
                cover_url =f'https:{cover_url}' #https://m.360buyimg.com/ceco/jfs/t1/133629/8/35466/60210/643a0c38Fc24d1f0f/fce0bdc036eb61fe.jpg!q70.jpg
                video_cover_url=cover_url.replace('!q70.jpg', '')

                try:
                    await page.wait_for_selector('div[class="shopbag-item-buybtn"]',timeout=1000)
                    print(f"{i}： 已发现识别到 buybtn ")     
                    time.sleep(random.randint(2, 4))               
                    await page.click('div[class="shopbag-item-buybtn"]')  # 点击购买按钮　转入新页面链接 　<div class="shopbag-item-buybtn">购买</div>
                    print(f"{i}： 已点击 购买,准备下载： ")
                except:
                    print(f"{i}： nonono-未发现识别到 商品链接 元素 ") 
                    await page.close() # 改多UA 2024.09.28====== 新加
                    continue
               
                await page.wait_for_timeout(2000)
                # while page.title()=='京东登录注册': #<title>京东登录注册</title>
                #     time.sleep(1)
                # await page.wait_for_timeout(1000)
                redirect_url =  page.url    
                # https://plogin.m.jd.com/login/login?returnurl=http%3A%2F%2Fitem.m.jd.com%2Fproduct%2F100051997121.html&appid=2146
                # https://plogin.m.jd.com/login/login?appid=2193&czLogin=1&returnurl=https%3A%2F%2Fitem.m.jd.com%2Fproduct%2F100044800682.html
                # https://trade.m.jd.com/common/limit.html?module=detail_m1&referer=http://item.m.jd.com/product/10076052437456.html
                # https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fh5.m.jd.com%2Factive%2Ffaxian%2Fvideo%2Findex.html%3Fid%3D564818116&czLogin=1
                # 这个网址是经过URL编码的，转换为正常网址后应该是：https://h5.m.jd.com/active/faxian/video/index.html?id=564818116


                
                if 'https://plogin.m.jd.com/login/login' in redirect_url: 
                    return_url = urllib.parse.unquote(redirect_url.split('returnurl=')[1].split('&')[0])
                    skuid = re.search(r'item.m.jd.com/product/(\d+).html', return_url).group(1)
                elif '//item.m.jd.com/product/' in redirect_url:
                    skuid = re.findall(r'//item.m.jd.com/product/(\d+).html', redirect_url)[0]
                elif 'wqs.jd.com/item/view.html' in redirect_url:
                    #https://wqs.jd.com/item/view.html?_fd=jx&sku=10113065457964&callback=skuInfoCB&source=h5v3&client=pg_apple&areaid=1_72_2819_0&fckr=&noWebpSupport=1&device_type=&isJson=1&fromRefer=https%3A%2F%2Fcfe.m.jd.com%2F&sceneval=2&buid=325&appCode=msc588d6d5&__navVer=1
                    skuid = re.search(r'sku=(\d+)&', redirect_url).group(1)    
                elif 'https://cfe.m.jd.com/' in redirect_url:
                    return_url = urllib.parse.unquote(redirect_url.split('returnurl=')[1].split('&')[0])
                    # http://item.m.jd.com/product/10062293929872.html
                    skuid = re.search(r'item.m.jd.com/product/(\d+).html', return_url).group(1)
                elif 'item.m.jd.com/product/' in redirect_url:
                    skuid = re.search(r'item.m.jd.com/product/(\d+).html', return_url).group(1) 
                # /product/10049006307165.html    
                else:  
                    print(f"{i}：没有得到skuid 转址：{redirect_url}")   
                    skuid = None

                if skuid:   
                    print(f"{i}：已取得skuid:{skuid},{video_title},尝试执行 download_video 下载...")  
                    # print(f"下载:{video_title}/{video_url}") 
                    # await download_video(skuid, video_title, video_url, video_cover_url, save_dir)               
                    try:
                        # print(f"下载:{video_title}/{video_url}") 
                        await download_video(skuid, video_title, video_url, video_cover_url, save_dir) # skuid, video_title, video_url, video_cover_url = video_info

                        await saveLog(i,video_title,skuid)
                        time.sleep(random.randint(2, 5))
                    except:
                        print(f"{i}：下载 出错***???***")  
                        continue  
                    await page.close() # 改多UA 2024.09.28====== 新加  
            else:
                await page.close() # 改多UA 2024.09.28====== 新加
                continue

            await page.close()    # 改多UA 2024.09.28====== 新加
            # await context.close() # 改多UA 2024.09.28====== 新加
        #END FOR 
        print("***完成***")        
        await browser.close()


def start_async_task(start_id, end_id, save_dir):
    asyncio.run(main(start_id, end_id, save_dir))

def buildComboBrPort():
    portList=[]
    portList=read_txt_file("browser_port.ini") #固定写入程序
    return portList

layout = [[sg.Text('采集开始ID号:'), sg.Input(key='start_id', default_text=start_id)],
          [sg.Text('采集结束ID号:'), sg.Input(key='end_id',   default_text=end_id)],
          [sg.Text('视频保存目录:'),sg.InputText(key="save_dir", default_text=big_dir ), sg.FolderBrowse() ],

          [sg.Output( size=(58, 12),font=("微软雅黑", 10), )], 
          [sg.Text('端口:',font=("微软雅黑", 10)),sg.Combo(buildComboBrPort(), size=(6,1),key="br_PORT",default_value=br_PORT,enable_events=True,),
           sg.Button('开始采集'),sg.Button('打开目录',button_color ='Green'),sg.Button('查看日志',button_color ='Green') , sg.Button('关闭程序',button_color ='Red')]]

window = sg.Window('18801京东视频采集程序V3-@liumingdada', layout,icon='iconJDV.ico')

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == '关闭程序':
        break
    elif event == '开始采集':
        start_id = int(values['start_id'])
        end_id = int(values['end_id'])
        save_dir_big = values['save_dir']
        saveConf(start_id,end_id,save_dir_big)

        # todayID_dir=f"{today_date}_{start_id}-{end_id}"
        todayID_dir=f"{today_date}_{end_id}"
        save_dir = os.path.join(save_dir_big, todayID_dir)
        

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        # asyncio.run(main(start_id, end_id, save_dir))

        # 创建一个线程并在其中运行asyncio任务
        thread = threading.Thread(target=start_async_task, args=(start_id, end_id, save_dir))
        thread.start()
    if event == '打开目录':
        end_id = int(values['end_id'])
        save_dir_big = values['save_dir']        
        todayID_dir=f"{today_date}_{end_id}"
        save_dir = os.path.join(save_dir_big, todayID_dir)
        os.startfile(save_dir)
    if event == '查看日志':
        today_date = datetime.datetime.today().strftime("%Y-%m-%d")# 获取今天的日期        
        log_file_path = f"downLog_{today_date}.txt"
        os.startfile(log_file_path)
        
    if event =='br_PORT':
        br_PORT=values['br_PORT']
        window.TKroot.title(f'{br_PORT}-JD达人多开辅助')
        print(f'浏览器 chrome.exe 远程调试的端口已选：{br_PORT}')    
    

       

window.close()

# pyinstaller -F -w -i iconJDV.ico 京东平台内视频采集V3.py 
#借鑑來源 簡書:https://www.jianshu.com/p/25a42d97185b

from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import cv2
import numpy as np
from io import BytesIO
import time,requests

class CrackSlider():

    #使用滑動驗證網站
    def __init__(self):
        self.url = 'https://member.igoldhk.com/'
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 20)
        self.zoom = 1

    #輸入帳戶資料
    def open(self):
        self.driver.get(self.url)
        self.wait.until(EC.presence_of_element_located((By.ID, 'userName')))
        self.driver.find_element_by_id('userName').send_keys('w201201')
        self.driver.find_element_by_id('password').send_keys('1qazxcde32wsx')
        time.sleep(0.5)

        #self.driver.find_element_by_id('userLogin').click()
        
    #獲得驗證圖片與小拼圖
    def get_pic(self):
        mouse = self.driver.find_element_by_class_name('slideCode_slider') #使用滑鼠懸停觸發驗證圖片顯示
        ActionChains(self.driver).move_to_element(mouse).perform()
        time.sleep(1)
        target = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'slideCode_bg-img'))) # 獲得有缺口的圖片
        template = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'slideCode_jigsaw'))) # 獲得小拼圖
        target_link = target.get_attribute('src')
        template_link = template.get_attribute('src')
        #print(target_link,template_link)
        target_img = Image.open(BytesIO(requests.get(target_link).content)) # 下載缺口圖片
        template_img = Image.open(BytesIO(requests.get(template_link).content)) # 下載小拼圖
        target_img.save('target.jpg')
        template_img.save('template.png')
        local_img = cv2.imread('target.jpg') # 使用opencv讀取缺口圖片
        size_loc = local_img.shape # 獲得缺口圖片大小(寬、高、頻道(彩色))
        print(size_loc)
        self.zoom = int(size_loc[0])/500 # 獲得缺口圖片寬度除以500數值當作結果值，作為縮放比例(拼圖移動會使用)

    def get_tracks(self, distance):
        print('distance : ',distance) # 顯示移動目的 X 座標
        distance += 10 # 模擬人為操作，拼圖移動超過缺口位置的距離
        v = 0 # 移動初速度
        t = 2 # 步進值
        forward_tracks = []
        current = 0
        mid = distance * 3 / 5  # 移動壘加的臨界值(下方判斷超過臨界值後執行遞減)，模擬人為操作拼圖快到缺口減速之動作
        while current < distance:
            if current < mid:
                a = 2  #加速度 2
            else:
                a = -3  #加速度-3
            s = v * t + 0.5 * a * (t ** 2)
            v = v + a * t
            current += s
            forward_tracks.append(round(s))
        print(forward_tracks)
        back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]
        return {'forward_tracks': forward_tracks, 'back_tracks': back_tracks}

    def match(self, target, template):
        img_rgb = cv2.imread(target) # 載入有缺口的圖片
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY) # 進行灰度化處理
        template = cv2.imread(template, 0) # 載入要搜索的圖片(可以滑動那張小拼圖)
        w, h = template.shape[::-1] # shape會顯示，寬、高與頻道(彩色3,灰諧1)，此處將最後一個數值del，因此紀錄小拼圖的圖像尺寸 W:寬 H:高
        print(w, h)

        # 開始進行匹配
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        # 得到兩組array，第一組因選擇TM_CCOEFF_NORMED，輸出值會式-1~1之間，第二組將會獲得第一組相對應的X座標位置
        # 判斷正確的位置便是當array[1]只剩下一個數值，及判斷圖片 X 座標
        run = 1

        # 使用二分法查找阈值的精确值
        L = 0
        R = 1
        while run < 20:
            run += 1
            threshold = (R + L) / 2
            print(threshold)
            if threshold < 0:
                print('Error')
                return None
            loc = np.where(res >= threshold)
            #print(loc)
            print(len(loc[1]))
            if len(loc[1]) > 1:
                L += (R - L) / 2
            elif len(loc[1]) == 1:
                print('缺口起始座標X位置：%d' % loc[1][0])
                break
            elif len(loc[1]) < 1:
                R -= (R - L) / 2
        return loc[1][0]

    # 移動拼圖
    def crack_slider(self,tracks):
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'slideCode_slider')))
        ActionChains(self.driver).click_and_hold(slider).perform()

        # 往右移動，使用forward_tracks列表當作移動軌跡
        for track in tracks['forward_tracks']:
            ActionChains(self.driver).move_by_offset(xoffset=track, yoffset=0).perform()

        time.sleep(0.5)

        # 往左移動，使用back_tracks列表當作移動軌跡
        for back_tracks in tracks['back_tracks']:
            ActionChains(self.driver).move_by_offset(xoffset=back_tracks, yoffset=0).perform()

        # 模擬人為操作"對準"之動作
        ActionChains(self.driver).move_by_offset(xoffset=-4, yoffset=0).perform()
        ActionChains(self.driver).move_by_offset(xoffset=4, yoffset=0).perform()
        time.sleep(0.5)

        ActionChains(self.driver).release().perform()

    def login(self):
        self.driver.find_element_by_id('userLogin').click()


if __name__ == '__main__':
    cs = CrackSlider()
    cs.open()
    while True:
        target = 'target.jpg'
        template = 'template.png'
        cs.get_pic()
        distance = cs.match(target, template)
        tracks = cs.get_tracks((distance + 7) * cs.zoom)  # 对位移的缩放计算
        cs.crack_slider(tracks)
        print('移動完成')
        time.sleep(1)
        try:
            cs.driver.find_element_by_class_name("slide_success")
            print("沒錯誤")
            break
        except:
            print("在一次")


    cs.login()

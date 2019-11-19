#借鑑來源 簡書:https://www.jianshu.com/p/25a42d97185b

#修正精準定位方式，增加功能註釋
#------運作方式------
#1.進入測試網站輸入會員資料，使用滑鼠懸停滑動控制板，觸發顯示並下載"驗證缺口圖片"與"小拼圖"。
#2.將驗證缺口圖片進行灰度處理後，使用opencv進行小拼圖比對，回傳缺口起始座標 X 位置。
#3.彈出視窗顯示，並標示偵測後缺口位置(此步驟為檢測使用，若正式運行，可移除此段)。
#4.依照前端顯示框架大小與實際圖片寬度製作 "比值" 倍數，將移動 X 距離乘以比值得到前端需移動總距離。
#5.使用漸進加速與左右來回橫移來模擬手動操作行為。
#6.確認成功元素或提示，程式終止結束。

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
        self.url = "https://xxx.test.com"
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 20)
        self.zoom = 1

    #輸入帳戶資料
    def open(self):
        self.driver.get(self.url)
        self.wait.until(EC.presence_of_element_located((By.ID,'userName')))
        self.driver.find_element_by_id('userName').send_keys('UserName')
        self.driver.find_element_by_id('password').send_keys('Password')
        time.sleep(0.5)

        #self.driver.find_element_by_id('userLogin').click()
        
    #獲得驗證圖片與小拼圖
    def get_pic(self):
        mouse = self.driver.find_element_by_class_name('slideCode_slider') # 使用滑鼠懸停觸發驗證圖片顯示
        ActionChains(self.driver).move_to_element(mouse).perform()
        # self.driver.find_element_by_class_name('slideCode_slider').click() # 使用滑鼠點擊也能觸發圖片(會刷新圖片)
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
        size_loc = local_img.shape # 獲得缺口圖片大小(高、寬、頻道(彩色))
        self.zoom = 400/int(size_loc[1]) # 網頁框架與實際圖片比例(拼圖移動會使用)，此處前端顯示寬度為400
    def get_tracks(self, distance):
        print('distance : ',distance) # 顯示移動目的 X 座標
        distance += 10 # 模擬人為操作，拼圖移動超過缺口位置的距離
        v = 0 # 移動初速度
        t = 2 # 步進值
        forward_tracks = []
        current = 0
        mid = distance * 3 / 5  # 移動壘加的臨界值(下方判斷超過臨界值後執行遞減)，模擬人為操作拼圖快到缺口減速之動作
        while True:
            if current < mid:
                a = 2  #加速度 2
            else:
                a = -3  #加速度-3
            s = v * t + 0.5 * a * (t ** 2)
            v = v + a * t
            current += s
            if current < distance:
                forward_tracks.append(round(s))
            else:
                forward_tracks.append(round(distance+s-current)) # 避免總移動長度超過目標缺口，最後一個移動距離為剩下的 X 距離
                break
        print(forward_tracks)
        back_tracks = [-3, -2, -2, -2, -1] #超過缺口後拼圖往左移動
        return {'forward_tracks': forward_tracks, 'back_tracks': back_tracks}

    def match(self, target, template):
        img_rgb = cv2.imread(target) # 載入有缺口的圖片
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY) # 進行灰度化處理
        template = cv2.imread(template, 0) # 載入要搜索的圖片(可以滑動那張小拼圖)
        w, h = template.shape[::-1] # shape會顯示，寬、高與頻道(彩色3,灰諧1)，此處將最後一個數值del，因此紀錄小拼圖的圖像尺寸 W:寬 H:高
        print(w, h)

        # 開始進行匹配
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        # res 會得到array，因選擇TM_CCOEFF_NORMED，輸出值會式-1~1之間，越靠近-1則代表較不符合，反之靠近1則代表越符合

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res) # 找尋array中最大值與最小值，以及相對應的位置
        print("最大值",max_loc,max_val)

        # 另外顯示匹配結果
        bottom_right = (max_loc[0] + w, h)
        img = cv2.rectangle(img_rgb, max_loc, bottom_right, (0, 255), 2)  # 劃出一個長方形(目標圖片,起始座標,相對座標,RGB顏色,線條寬度 )
        print("目標座標範圍 :\nx:%r - %r\ny:%r - %r" % (max_loc[0], bottom_right[0], max_loc[1], bottom_right[1]))
        cv2.imwrite('target_OK.jpg', img)
        cv2.imshow('Find_target', img) # 彈出視窗並顯示標示畫線區域結果
        cv2.waitKey(0) # 等待任何按鍵觸發
        cv2.destroyAllWindows() # 關閉顯示畫線圖片(target_OK)

        return max_loc[0]

        # run = 1
        # 使用二分法查找阈值的精确值
        # L = 0
        # R = 1
        # while run < 20:
        #     run += 1
        #     threshold = (R + L) / 2
        #     print(threshold)
        #     if threshold < 0:
        #         print('Error')
        #         return None
        #     loc = np.where(res >= threshold)
        #     if len(loc[1]) > 1:
        #         L += (R - L) / 2
        #     elif len(loc[1]) == 1:
        #         print('缺口起始座標X位置：%d' % loc[1][0])
        #         break
        #     elif len(loc[1]) < 1:
        #         R -= (R - L) / 2



    # 移動拼圖
    def crack_slider(self,tracks):
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'slideCode_slider')))
        ActionChains(self.driver).click_and_hold(slider).perform() #滑鼠左鍵持續按著不放

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

        ActionChains(self.driver).release().perform() # 釋放滑鼠左鍵

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
        tracks = cs.get_tracks((distance)* cs.zoom) # 移動距離乘以"網頁"與"實際圖片"寬度的比值。
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

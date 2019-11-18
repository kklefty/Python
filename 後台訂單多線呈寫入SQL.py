# 主程式運行
# --------運行功能----------
# 至Web後台搜尋訂單，(上個月最後一日 ~ 本月份全天)
# 將訂單搜尋以每5日進行一個線呈，同時併發運行。
# 獲得數據後，儲存HTML代碼，分析拆解信息
# 確認訂單編號，在資料庫與目前下載的內容無重複，變執行寫入資料庫中
# -------------------------


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread
from bs4 import BeautifulSoup
import pymysql
import calendar
import time


def work(start_day,end_day):
    # 後台查詢條件
    supplier_name = 'MY.HSR'


    # 連接MySQL
    conn = pymysql.connect(db='alex', user='alex', passwd='0000', host='2213-server.ddns.net',charset="utf8", port=5307)
    cursor = conn.cursor()


    # 使用Selenium進入後台爬取資料
    # -----使用有option的driver可以不顯示視窗------
    # option = webdriver.ChromeOptions()
    # option.add_argument('headless')
    # driver = webdriver.Chrome(chrome_options=option)
    # -------------------------------------------
    driver = webdriver.Chrome()
    driver.get("https://xxxx.xxx.com")
    # 登入
    driver.find_element_by_name("username").send_keys('UserName')
    driver.find_element_by_name("password").send_keys('Password')
    driver.find_element_by_xpath("//*[@id='login']/div[4]/div[2]/button").click()

    # 進入首頁
    element = WebDriverWait(driver,10).until(EC.visibility_of_element_located((By.LINK_TEXT,"單據管理")))# 等待葉面數據載入完成，避免網路緩慢造成錯誤
    # 進入請款單頁面(已完成登入，cookie允許訪問深層頁面)
    driver.get("https://xxxx.xxx.com/collect/add")
    driver.find_element_by_id("begCrtDt").send_keys(start_day) # begCrtDt begLstGoDt
    driver.find_element_by_id("endCrtDt").send_keys(end_day) # endCrtDt endLstGoDt
    driver.find_element_by_id("supplierName").send_keys(supplier_name)
    sel = Select(driver.find_element_by_id("prodCurrCd"))# 下拉式選單
    sel.select_by_value("TWD")
    # 確認按鈕為Javascript動態轉圈，必須使用JS點擊才可成功送出請求
    element = driver.find_element_by_id('searchBtn')
    driver.execute_script("arguments[0].click();", element)
    # 等待Ajax回應搜尋內容，監測為"共應商編號: 供應商名稱:" 若已成為顯示狀態，即可繼續執行
    WebDriverWait(driver,15).until(EC.visibility_of_element_located((By.XPATH,"//*[@id='ngApp']/div/div[2]/div[1]/div[2]/h4")))
    print('數據下載完成,準備寫入資料庫')
    html = driver.page_source
    # -----將目前網頁HTML code存入文本中-----
    # with open("html.txt",'w',encoding='UTF-8') as f:
    #     f.write(html)
    # --------------
    driver.close()
    driver.quit()


    # MySQL搜尋供應商對應ID
    sql = "SELECT * FROM web_supplier_tab WHERE supplier_name = '%s'" % supplier_name
    cursor.execute(sql)
    findobj = cursor.fetchone()# 取得第一個查詢到的結果
    supplier_id = int(findobj[0])

    # BS4分析切割網頁HTML code
    obj=BeautifulSoup(html)
    #資料寫在tbody列表裡面，取出進行分解。
    f = obj.find("tbody").findAll("tr",{"class":"ng-scope"})

    def domyfind(ta,nb,sl):# 切割兩行數據內容，取單行資料並消除空格
        ans = ta[nb].get_text()
        return ans.split("\n")[sl].strip()

    for targe in f:
        #尋找每一行
        tag = targe.findAll("td")
        #訂單編號
        ordnbr = domyfind(tag,1,2)
        #訂購日與發貨日
        ord_date = domyfind(tag,2,1)[0:10]
        set_off_date = domyfind(tag,2,2)[0:10]
        #訂單狀態
        status = domyfind(tag,4,1)
        #搜尋狀態對應代碼ID
        try:
            sql = "SELECT * FROM web_status_tab WHERE status_name = '%s'" % status
            cursor.execute(sql)
            findobj = cursor.fetchone()
            status_id = int(findobj[0])
        except:
            status_id = 5
        #商品編號
        commodity_nbr = domyfind(tag,5,1)
        #商品名稱
        commodity =domyfind(tag,6,1)
        #商品內容
        commodity_content = tag[7].input.attrs['value']#此欄位使輸入欄位，系統預設數據須重attr取出
        #成本
        cost = tag[10].input.attrs['value']#此欄位使輸入欄位，系統預設數據須重attr取出
        #print (ordnbr,ord_date,set_off_date,status,commodity_nbr,commodity,commodity_content,cost)


        #確認資料庫沒有相同的訂單編號
        sql = "SELECT * FROM web_report WHERE ordnbr = '%s'" % ordnbr
        cursor.execute(sql)
        findobj = cursor.fetchone()
        if findobj==None:
            # 將搜尋資料寫入資料庫
            sql = "INSERT INTO web_report(supplier_id,ordnbr,ord_date,set_off_date,status_id,commodity_nbr,commodity,commodity_content,cost)VALUE('%d','%s','%s','%s','%s','%s','%s','%s','%s')" % (
            supplier_id, ordnbr, ord_date, set_off_date, status_id, commodity_nbr, commodity, commodity_content, cost)
            cursor.execute(sql)
            conn.commit()
            print("%r wirt ok"%ordnbr)
        else:
            print("訂單編號 : "+findobj[2]+" 已存在。")
    cursor.close()
    conn.close()





# --------條件設置----------
# now_year = 2018 # 手動設定年份
# now_mounth = 5 # 手動設定月份
now_year = time.localtime(time.time()).tm_year # 自動獲取系統目前年份
now_mounth = time.localtime(time.time()).tm_mon # 自動獲取系統目前月份

# 跨年分調整
if now_mounth == 1:
    lest_mounth = 12
    lest_year = now_year-1
else:
    lest_mounth = now_mounth-1
    lest_year = now_year

end_day = calendar.monthrange(now_year,now_mounth)
lest_day = calendar.monthrange(lest_year,lest_mounth)
end_day = end_day[1]
lest_day = lest_day[1]

first_date = "%d-%d-%d"%(lest_year,lest_mounth,lest_day) # 開始日期
end_date = "%d-%d-%d"%(now_year,now_mounth,end_day) # 結束日期
do_month = "%d-%d-"%(now_year,now_mounth) # 年+月


# -------多線呈任務-----------
date =[[first_date,"%s5"%do_month],
       ["%s6"%do_month,"%s10"%do_month],
       ["%s11"%do_month,"%s15"%do_month],
       ["%s16"%do_month,"%s20"%do_month],
       ["%s21"%do_month,"%s25"%do_month],
       ["%s26"%do_month,end_date]
]

th_list=[]
for i in date:
    th=Thread(target=work,args=(i[0],i[1]))
    th.start()
    th_list.append(th)
    print('%s線成執行中'%i)
for j in th_list:
    j.join()

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 크롬 드라이버 자동 업데이트
from webdriver_manager.chrome import ChromeDriverManager
# 날짜 라이브러리
from datetime import date, timedelta
import mysql_auth
import pymysql

# 각종 설정

# 브라우저 자동꺼짐 방지
chrome_options = Options()
# 창없이
chrome_options.add_argument('--headless')
chrome_options.add_experimental_option("detach", True)
# 불필요한 에러 메시지 없애기
chrome_options.add_experimental_option("excludeSwitches", ['enable-logging'])
service = Service(executable_path='chromedriver.exe')
driver = webdriver.Chrome(service=service, options=chrome_options)

# 각종 만든 함수

# 페이지 로딩 기다렸다가 클릭
def like_text_click_wait(tag, elem):
    x_path = '//{0}[contains(text(), "{1}")]'.format(tag, elem)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, x_path)))
    driver.find_element(By.XPATH, x_path).click()
    print(' {0} 클릭 완료 !!    태그: {1} '.format(elem, x_path))


def text_click_wait(tag, elem):
    x_path = '//{0}[text() = "{1}"]'.format(tag, elem)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, x_path)))
    driver.find_element(By.XPATH, x_path).click()
    print(' {0} 클릭 완료 !!    태그: {1} '.format(elem, x_path))


# 주소 이동
url = "https://flight.naver.com"
driver.get(url)

# 달력 창 이동
begin_date = driver.find_element(By.XPATH, '//button[text() = "가는 날"]')
begin_date.click()
# 출발 일정 으로 내일 날짜 클릭
tomorrow = date.today().day + 1
departDay = driver.find_elements(By.XPATH, '//b[text() = "{0}"]'.format(tomorrow))[0]
departDay.click()
# 도착 일정 으로 3박4일 날짜 클릭
arriveDay = driver.find_elements(By.XPATH, '//b[text() = "{0}"]'.format(tomorrow + 4))[0]
arriveDay.click()

# 도착지 설정 클릭
text_click_wait('b', '도착')
# destination = driver.find_element(By.XPATH, '//b[text() = "도착"]')
# destination.click()
# 도착 국가 일본 클릭
text_click_wait('button', '일본')
# 도착 공항 간사이 공항 클릭
text_click_wait('i', '간사이국제공항')

# 해당 일정 으로 조회
like_text_click_wait('span', '검색')


# 로딩바 사라 질 때까지 대기
wait = WebDriverWait(driver, 30)
loading_progress = wait.until(EC.presence_of_element_located((By.CLASS_NAME, '''loadingProgress_progress__2ckqJ''')))
wait.until(EC.staleness_of(loading_progress))
print("==============================로딩완료==============================")

# 카드 혜택 제외
text_click_wait('button', '포함')
text_click_wait('span', '제외')
# 티켓 정보
ticket_info = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.XPATH, '''//div[@class="concurrent_ConcurrentItemContainer__2lQVG result"]''')))

# 티켓 리스트 생성
ticket_list = [str(x+1) +" " + ticket_info[x].text.replace("\n", " ") for x in range(10)]

# 공백 제거, 불필요한 데이터 제거
replace_list = []
for x in ticket_list:
    replace_x = x.replace("성인/모든 결제수단", "").replace("이벤트혜택", "").replace("직항", "").replace("왕복", "").replace(",", "").replace("   ", " ").replace("  ", " ")
    replace_list.append(replace_x)

login = mysql_auth.lnfo
# MySQL 연결
conn = pymysql.connect(host=login['host'], port=login['port'],
                       user=login['user'], passwd=login['passwd'],
                       db=login['db'], charset=login['charset'])
# Cursor 생성
cur = conn.cursor()

sql = """
        INSERT INTO BD_TICKET_CRAWLING
        (TICKET_RANK, DEPT_DAY, DEPT_CITY, DEPT_AIRLINE, DEPT_TIME,
         ARRV_DAY, ARRV_CITY, ARRV_AIRLINE, ARRV_TIME, PRICE)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

for x in replace_list:
    ticket = x.split(" ")
    rank = ticket[0]
    month = str(date.today().month)
    today = date.today().day
    depart_day = month + "월" + str(today + 1) + "일"
    depart_airline = ticket[1]
    depart_randing_time = ticket[2][:5]
    depart_city = ticket[2][5:]
    arrive_day = month + "월" + str(today + 5) + "일"
    if ticket[6][0].isdigit():
        ticket.insert(6, depart_airline)
    arrive_airline = ticket[6]
    arrive_randing_time = ticket[7][:5]
    arrive_city = ticket[7][5:]
    price = ticket[-1]

    # SQL 실행
    cur.execute(sql, (rank, depart_day, depart_city, depart_airline, depart_randing_time, arrive_day, arrive_city, arrive_airline, arrive_randing_time, price))
# 데이터 커밋
conn.commit()
# 연결 종료
conn.close()

import json
import os
import pathlib
import shutil
import time
from pathlib import Path
from urllib.parse import urljoin

import PyPDF2
import pdfkit
import requests
from bs4 import BeautifulSoup
from natsort import natsorted, ns
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def create_save_path(name):
    # save_directory = get_jreast_station_name(soup)
    save_path = os.path.join('pdf', name)
    print(name)

    if name not in os.listdir('./pdf'):
        os.mkdir(save_path)

    return save_path


def download_pdfs(timetable_urls, name):
    save_path = create_save_path(name)

    count = 0
    for timetable_url in timetable_urls:
        if 'timetable-v' not in timetable_url:
            count += 1
            create_pdf(timetable_url, count, save_path)

    merge_pdf_files(save_path, name)


# https://degitalization.hatenablog.jp/entry/2021/03/13/102805
def create_pdf2(url, count, save_path):
    save_file_path = os.path.join(save_path, str(count) + '.pdf')
    print('url: ' + url)
    print('save_file_path: ' + save_file_path)

    # 印刷としてPDF保存する設定
    options = webdriver.ChromeOptions()
    app_state = {
        "recentDestinations": [
            {
                "id": "Save as PDF",
                "origin": "local",
                "account": ""
            }
        ],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
        "isLandscapeEnabled": False,  # 印刷の向きを指定 tureで横向き、falseで縦向き。
        "pageSize": 'A4',  # 用紙タイプ(A3、A4、A5、Legal、 Letter、Tabloidなど)
        # "mediaSize": {"height_microns": 355600, "width_microns": 215900}, #紙のサイズ　（10000マイクロメートル = １cm）
        # "marginsType": 0, #余白タイプ #0:デフォルト 1:余白なし 2:最小
        # "scalingType": 3 , #0：デフォルト 1：ページに合わせる 2：用紙に合わせる 3：カスタム
        # "scaling": "141" ,#倍率
        # "profile.managed_default_content_settings.images": 2,  #画像を読み込ませない
        "isHeaderFooterEnabled": False,  # ヘッダーとフッター
        "isCssBackgroundEnabled": True,  # 背景のグラフィック
        # "isDuplexEnabled": False, #両面印刷 tureで両面印刷、falseで片面印刷
        # "isColorEnabled": True, #カラー印刷 trueでカラー、falseで白黒
        # "isCollateEnabled": True #部単位で印刷
    }
    path = pathlib.Path(save_path)
    print(f'path: {path}')
    print(path.resolve())

    prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(app_state),
             'download.default_directory': '.\\pdf\\JR武蔵中原\\'
             # 'download.default_directory': '~/Downloads'
             }  # app_state --> pref
    options.add_experimental_option('prefs', prefs)  # prefs --> chopt
    options.add_argument("--headless=new")
    options.add_argument('--kiosk-printing')  # 印刷ダイアログが開くと、印刷ボタンを無条件に押す。

    driver_path = r'.\chromedriver\chromedriver.exe'
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)  # 秒 暗示的待機
    driver.get(url)  # URL 読み込み
    WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)  # ページ上のすべての要素が読み込まれるまで待機（15秒でタイムアウト判定）
    # driver.execute_script('return window.print()')  # Print as PDF
    driver.execute_script('window.print();')
    time.sleep(10)  # ファイルのダウンロードのために10秒待機
    driver.quit()  # Close Screen

    # WebページをPDF出力
    # pdfkit.from_url(url, save_file_path, options=options, configuration=config)


def create_pdf(url, count, save_path):
    options = {
        'page-size': 'A4',
        'margin-top': '0.1in',
        'margin-right': '0.1in',
        'margin-bottom': '0.1in',
        'margin-left': '0.1in',
        'encoding': "UTF-8",
        'no-outline': None,
        'disable-smart-shrinking': '',
        # 'orientation': 'Landscape',
    }

    config_path = r'.\wkhtmltox\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=config_path)

    # WebページをPDF出力
    save_file_path = os.path.join(save_path, str(count) + '.pdf')
    print('url: ' + url)
    print('save_file_path: ' + save_file_path)
    pdfkit.from_url(url, save_file_path, options=options, configuration=config)


def merge_pdf_files(save_path, pdf_name):
    # フォルダ内のファイルを自然数字順でソートする（1,2,...,11,12,...）
    pdf_files = natsorted(Path(save_path).glob('*.pdf'), key=lambda x: os.path.basename(x), alg=ns.REAL)
    pdf_writer = PyPDF2.PdfFileWriter()

    for pdf_file in pdf_files:
        pdf_reader = PyPDF2.PdfFileReader(str(pdf_file))
        for i in range(pdf_reader.getNumPages()):
            pdf_writer.addPage(pdf_reader.getPage(i))

    # フォルダを削除する
    shutil.rmtree(save_path)

    # ファイルは1つ上位のフォルダに作成する
    merged_file = os.path.join(os.path.join(save_path, '../'), pdf_name) + '.pdf'
    with open(merged_file, "wb") as f:
        pdf_writer.write(f)


# def get_jreast_station_name(soup):
#     station_name = soup.select_one('h1.station_name01').string
#     return 'JR' + station_name


# 印刷用ページはpが必要
def get_jreast_print_url(url):
    return url.replace('.html', 'p.html')


def search_jreast_timetable_urls(url, name):
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    timetable_urls = []

    # <td class="weekday"><a href="../2102/timetable/tt0307/0307010.html">平日</a></td>
    # -> <a href="../2102/timetable/tt0307/0307010.html">平日</a>
    a_tags = soup.select('td.weekday a')
    for a in a_tags:
        # 相対パスになっているので，URLを結合して絶対パスに変換する
        timetable_urls.append(get_jreast_print_url(urljoin(url, a['href'])))

    # <td class="holiday"><a href="../2102/timetable/tt0307/0307011.html">土曜・休日</a></td>
    # -> <a href="../2102/timetable/tt0307/0307011.html">土曜・休日</a>
    a_tags = soup.select('td.holiday a')
    for a in a_tags:
        # 相対パスになっているので，URLを結合して絶対パスに変換する
        timetable_urls.append(get_jreast_print_url(urljoin(url, a['href'])))
    print(timetable_urls)

    download_pdfs(timetable_urls, name)


def search_jorudan_timetable_urls(url, name):
    timetable_urls = [url + '?&Dw=1', url + '?&Dw=3']

    download_pdfs(timetable_urls, name)


def search_tokyu_timetable_urls(url, name):
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    timetable_urls = []

    # <li class="mod-timetable_list_item">
    # <a href="http://transfer.navitime.biz/tokyu/pc/diagram/TrainDiagram?stCd=00007965&rrCd=00000790&updown=1" target="_blank">
    # <dl>
    # <dt>下り</dt>
    # <dd>元町・中華街方面（※）<span class="mod-icon-blank">（別窓で開く）</span></dd>
    # </dl>
    # </a>
    a_tags = soup.select('li.mod-timetable_list_item a')
    for a in a_tags:
        if 'class' in a.attrs:
            continue
        timetable_urls.append(a['href'])

    download_pdfs(timetable_urls, name)


# 元は http://www.jr-odekake.net/eki/timetable.php?id=0610135 などのURLだが，
# このページのjs内にある https://mydia.jr-odekake.net/cgi-bin/district2/2815.html
# などのURLからスタートする
def search_jrwest_timetable_urls(url, name):
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    timetable_urls = []

    a_tags = soup.select('td[scope="row"] a')
    for a in a_tags:
        url_today = a['onclick'].split('\'')[1]
        # url_holiday = url_today + '&yearmonth=20210307&x=28&y=11'
        timetable_urls.append(url_today)

    print(timetable_urls)

    download_pdfs(timetable_urls, name)


def main_function(url, name):
    if 'jreast' in url:
        search_jreast_timetable_urls(url, name)
    elif 'jorudan' in url:
        search_jorudan_timetable_urls(url, name)
    elif 'tokyu' in url:
        search_tokyu_timetable_urls(url, name)
    elif 'jr-odekake' in url:
        search_jrwest_timetable_urls(url, name)


if __name__ == '__main__':
    file_name = './input_url_list.txt'
    with open(file_name, 'r', errors='replace', encoding="utf_8") as file:
        line_list = file.readlines()

    line_count = 0

    for line in line_list:
        line_count += 1
        input_url = line.split(',')[0]
        file_name = line.split(',')[1].replace('\n', '')
        print(line_count, '/', len(line_list))
        print('input_url: ' + input_url)
        main_function(input_url, file_name)

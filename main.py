import os
import shutil
from pathlib import Path
from urllib.parse import urljoin

import requests
import pdfkit
from bs4 import BeautifulSoup

import PyPDF2
from natsort import natsorted, ns


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
    }

    config_path = r'.\wkhtmltox\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=config_path)

    # WebページをPDF出力
    # url = 'https://www.jreast-timetable.jp/2102/timetable/tt0307/0307010p.html'
    save_file_path = os.path.join(save_path, str(count) + '.pdf')
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


def get_jreast_station_name(soup):
    station_name = soup.select_one('h1.station_name01').string
    return 'JR' + station_name


# 印刷用ページはpが必要
def get_jreast_print_url(url):
    return url.replace('.html', 'p.html')


def search_jreast_timetable_urls(url):
    res = requests.get(url)
    res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, 'html.parser')
    save_directory = get_jreast_station_name(soup)
    save_path = os.path.join('pdf', save_directory)
    print(save_directory)

    if save_directory not in os.listdir('./pdf'):
        os.mkdir(save_path)

    timetable_urls = []

    # <td class="weekday"><a href="../2102/timetable/tt0307/0307010.html">平日</a></td>
    # -> <a href="../2102/timetable/tt0307/0307010.html">平日</a>
    a_tags = soup.select('td.weekday a')
    for a in a_tags:
        # 相対パスになっているので，URLを結合して絶対パスに変換する
        timetable_urls.append(urljoin(url, a['href']))

    # <td class="holiday"><a href="../2102/timetable/tt0307/0307011.html">土曜・休日</a></td>
    # -> <a href="../2102/timetable/tt0307/0307011.html">土曜・休日</a>
    a_tags = soup.select('td.holiday a')
    for a in a_tags:
        # 相対パスになっているので，URLを結合して絶対パスに変換する
        timetable_urls.append(urljoin(url, a['href']))
    # print(timetable_urls)

    count = 0
    for timetable_url in timetable_urls:
        count += 1
        create_pdf(get_jreast_print_url(timetable_url), count, save_path)

    merge_pdf_files(save_path, save_directory)


def main_function(url):
    if 'jreast' in url:
        search_jreast_timetable_urls(url)


if __name__ == '__main__':
    file_name = './input_url_list.txt'
    with open(file_name, 'r', errors='replace') as file:
        input_url_list = file.readlines()

    line_count = 0

    for input_url in input_url_list:
        line_count += 1
        input_url = input_url.split(',')[0]
        print(line_count, '/', len(input_url_list))
        print('input_url: ' + input_url)
        main_function(input_url)

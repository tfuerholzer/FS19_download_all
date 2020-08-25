import http.client
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import urlopen as httpget

from bs4 import BeautifulSoup

OUTPUT_PATH = "C:/lsmods"
MAX_PAGES = 200
BASE_URL = 'https://farming-simulator.com/mods.php?lang=de&country=de&title=fs2019&filter=latest&page='
BASE_FINAL_URL = 'https://farming-simulator.com/'
URL_FORMAT = '{}{}'
DOWNLOAD_FILE_THREADS = 15
ALL_URLS = []
BANNED_CATEGORIES = ['Gameplay', 'Prefab']

download_bound_pool = ThreadPoolExecutor(max_workers=DOWNLOAD_FILE_THREADS)


def foreach(future_list, callback):
    print(future_list)
    result_list = future_list.result()
    print(result_list)
    for e in result_list:
        callback(e)


def generate_url(number):
    return URL_FORMAT.format(BASE_URL, number)


def extract_from_row(row):
    row["medium-6 large-3 columns"]["mod-item"]["button button-buy button-middle button-no-margin expanded"]


def starts_with_mod_php(url):
    return url.startswith('mod.php')


def build_mod_link(mod_url):
    if mod_url.find('mod_id='):
        return BASE_FINAL_URL + mod_url


def extract_mod_download_url(page, banned_categories):
    page = BeautifulSoup(page, 'html.parser')
    try:
        category = \
            page.find('div', {'class': 'table table-game-info'}).find_all('div', recursive=False)[2].find_all('div')[
                1].get_text()
        if category in banned_categories:
            return None
        else:
            return page.find('a', {'class': 'button button-buy button-middle button-no-margin expanded'})['href']
    except:
        return None


def get_mod_page_links_form_page(html_data):
    data = []
    soup_page = BeautifulSoup(html_data, 'html.parser')
    for link in soup_page.find_all('a', {'class': 'button button-buy button-middle button-no-margin expanded'}):
        mod_url = link['href']
        data.append(build_mod_link(mod_url))
    return data


def extract_filename_from_download_url(download_url):
    index = download_url.rfind('/')
    return download_url[index:len(download_url)]


def try_download(download_url, download_filename):
    try:
        out_file = open(OUTPUT_PATH + download_filename, "xb")
        connection_string = download_url[8: download_url.find('.com') + 4]
        mod_id_startindex = download_url.find('storage/') + len('storage/')
        mod_id = download_url[mod_id_startindex: mod_id_startindex + 8]
        payload = ''
        conn = http.client.HTTPSConnection(connection_string)
        headers = {
            'authority': connection_string,
            'upgrade-insecure-requests': '1',
            'Upgrade-Insecure-Requests': '1',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
            'Referer': 'https://farming-simulator.com/mod.php?lang=de&country=de&mod_id=' + mod_id[2: len(
                mod_id)] + '&title=fs2019'
        }
        conn.request("GET", '/modHub/storage/' + mod_id + '/' + download_filename, payload, headers)
        res = conn.getresponse()
        data = res.read()
        out_file.write(data)
    except:
        print(download_filename + " is already downloaded!")


def download_mods(number):
    url = generate_url(number)
    main_page = httpget(url).read()
    mod_page_urls = get_mod_page_links_form_page(main_page)
    for url in mod_page_urls:
        mod_page = httpget(url).read()
        download_url = extract_mod_download_url(mod_page, BANNED_CATEGORIES)
        if not download_url is None:
            filename = extract_filename_from_download_url(download_url)
            print('downloading :' + filename)
            download_bound_pool.submit(try_download(download_url, filename))


max_pages_range = range(0, MAX_PAGES)
for i in max_pages_range:
    download_mods(i)

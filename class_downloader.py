import requests
from bs4 import BeautifulSoup
import re
import json
from requests.packages import urllib3
import os
from time import sleep
import requests
import zipfile
import io
from new_converter import Converter
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = ''
PASSWORD = ''

# credit goes to greenstick https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    # Print New Line on Complete
    if iteration == total:
        print()


class Lms:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self._links = []
        self.downloaded_files_folder = 'Adobe_Download_Files'
        self.download_folder = os.path.join(os.path.expanduser(
            '~'), 'Downloads', self.downloaded_files_folder)
        self.agent_cookie = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
        self.host = ''
        self.headers = {
            'User-Agent': self.agent_cookie
        }
        self.__session = requests.Session()
        if not os.path.isdir(self.download_folder):
            os.makedirs(self.download_folder)

    def __class_list(self):
        _session = requests.Session()
        html = _session.post(
            'http://vu.sbu.ac.ir/vu99/course.list.php', data={'username': self.username}).text
        _classes = BeautifulSoup(html, 'html.parser')

        for cl in _classes.select('a[href^="https://lms"]'):
            self._links += [(cl.text, cl['href'])]

    def __login(self):
        self.__session.get('https://'+self.host +
                           '/login/index.php', verify=False)
        self.__session.post('https://'+self.host+'/login/index.php', data={
                            'username': self.username, 'password': self.password}, headers=self.headers, verify=False)
        self.__set_headers(self.host)

    def __session_list(self, course):
        self.__login()

        html = BeautifulSoup(self.__session.get(
            self._links[course][1], headers=self.headers, verify=False).text, 'html.parser')
        html_course = BeautifulSoup(self.__session.get(html.select('li.onlineclass div.activityinstance > a')[
                                    0]['href'] + '&action=recording.list', headers=self.headers, verify=False).text, 'html.parser')
        _courses = html_course.select(
            'a[href^="/mod/onlineclass"][target="_blank"]')

        return _courses

    def __get_cookies(self, domain):
        _session_cookies = ''
        for cookie, value in self.__session.cookies.get_dict(domain=domain).items():
            _session_cookies += f'{cookie}={value};'

        return _session_cookies

    def get_server(self, no):
        if no == 1:
            _base_url = 'http://vc10.sbu.ac.ir'
        elif no == 2:
            _base_url = 'http://vc15.sbu.ac.ir'

        return _base_url

    def __set_headers(self, domain):
        self.headers['Cookie'] = self.__get_cookies(domain)
        return self.headers

    def __get_download_url(self, class_session):
        self.video_id = re.search(
            "(?<=url=).+?(?=&)", self.__classes[class_session]["href"]).group(0)
        self.adobe_server = self.get_server(
            int(self.__classes[class_session]['href'][-1]))
        self.__session.get('https://'+self.host + self.__classes[class_session]['href'], headers={
            'User-Agent': self.agent_cookie}, verify=False)
        _download_url = self.adobe_server + \
            f'/{self.video_id}' + '/output' + \
            f'/{self.video_id}.zip?download=zip'
        return _download_url

    def __get_cookies_from_adobe_server(self):
        r = self.__session.get(f'{self.adobe_server}/system/get-player?urlPath=/{self.video_id}/',
                               headers={'User-Agent': self.agent_cookie})
        self.__session.cookies.set(r.headers['Set-Cookie'].split(';')[0].split('=')[
                                   0], r.headers['Set-Cookie'].split(';')[0].split('=')[1], path='/', domain=self.adobe_server[7:])
        self.__set_headers(self.adobe_server.split('/')[-1])

    def __download__(self, url):
        self.__get_cookies_from_adobe_server()
        zip_file = os.path.join(self.download_folder, self.video_id + '.zip')
        current_size = 0

        with open(zip_file, 'wb') as f:
            current_size = 0
            with self.__session.get(url, headers=self.headers, stream=True) as r:
                total_size = int(r.headers['content-length'])
                try:
                    print(
                        f'Downloading ...\nFile size [{round(int(r.headers["content-length"]) / 10 ** 6, 3)}MB]')
                except:
                    raise ValueError('Site is not accessible!')
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
                    current_size += sys.getsizeof(chunk)
                    printProgressBar(current_size, total_size)

        z = zipfile.ZipFile(zip_file)
        print('Download compeleted ...')
        print('Extracting ...')
        z.extractall(os.path.join(self.download_folder, self.name))
        print('Extract Compeleted ...')
        print('Removing zip file')
        os.remove(zip_file)
        print('zip file removed')

    # the main program
    def run(self):
        self.__class_list()
        for index, l in enumerate(self._links):
            print(f'{index}:' + re.sub(r"\(.+?\)", "", l[0]))

        print(30*'-')
        _course = int(input('Enter your course index: '))
        print(30*'-')

        self.host = self._links[_course][1].split('/')[2]

        self.__classes = self.__session_list(_course)

        for index, s in enumerate(self.__classes):
            print(f'{index}:{s.parent.text}')

        print(30*'-')
        _class_session = int(input('Enter the session index: '))
        print(30*'-')

        print(30*'-')
        self.name = input('Enter the name of the folder: ')
        print(30*'-')

        self.__download__(self.__get_download_url(_class_session))


l = Lms(USERNAME, PASSWORD)
l.run()

f = Converter(os.path.join(l.download_folder, l.name))
f.convert(l.name, 'video')

import requests
import random


class AccessDenied(Exception):
    pass


class Sess:
    def __init__(self):
        self.ses = requests.session()
        self.agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"]
        self.headers = {"User-Agent": random.sample(self.agents,1)[0]}
        self.proxies = None
        self.counter = 0
        self.list_proxies  = ["154.16.52.198","185.145.36.203", "185.158.105.238",
"185.158.150.220", "191.101.85.126"]
    def reset_ses(self):
        self.ses = requests.session()

    def reset_counter(self):
        self.counter = 0
    def get(self, url):
        if self.counter >= 3:
            self.reset_counter()
            return False
        self.counter += 1
        response = self.ses.get(url, headers=self.headers, proxies = self.proxies)
        if response.status_code != 200:
            self.reset_agent()
            self.use_proxy()
            return self.get(url)
        self.reset_counter()
        if response.status_code != 200:
            raise AccessDenied
        return response

    def reset_agent(self):
        if len(self.agents) > 0:
            self.headers["User-Agent"] = random.sample(self.agents,1)[0]
        else:
            raise Exception("no other agent to use")
        return True


    def use_proxy(self):


        prox = random.sample(self.list_proxies,1)[0]
        proxyDict = {
            "http":  f'http://e1ea0c39a5:xERy6ScT@{prox}:4444',
            "https": f'https://e1ea0c39a5:xERy6ScT@{prox}:4444',
        }
        self.proxies = proxyDict
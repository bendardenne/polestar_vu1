from enum import Enum
from threading import Thread
from time import sleep

import requests


class ChargeState(Enum):
    IDLE = 0
    CHARGING = 1
    CHARGED = 2
    ERROR = 3


class Blinker:
    active = False
    on = False
    state = ChargeState.IDLE

    def __init__(self, publisher, delay):
        self.publisher = publisher
        self.delay = delay
        self.thread = Thread(target=self.__loop, daemon=True)
        self.thread.start()

    def start(self, state):
        self.active = True
        self.state = state

    def stop(self):
        self.active = False

    def __loop(self):
        while True:
            sleep(self.delay)
            if not self.active:
                continue
            self.__do_blink()

    def __do_blink(self):
        if self.state == ChargeState.CHARGING:
            self.publisher(0, 100 if self.on else 0, 0)
        elif self.state == ChargeState.ERROR:
            self.publisher(100 if self.on else 0, 0, 0)
        self.on = not self.on


class PolestarStatusUpdater:
    state = ChargeState.IDLE
    soc = 0
    blinking = False

    def __init__(self, vu_url, api_key):
        self.url = vu_url
        self.api_key = api_key
        self.blinker = Blinker(publisher=self.__publishColor, delay=2)

    def publish(self, state, soc):
        self.state = state
        self.soc = soc
        self.__publishSoc()

        if self.state in [ChargeState.CHARGING, ChargeState.ERROR]:
            self.blinker.start(self.state)
        elif self.state == ChargeState.CHARGED :
            self.blinker.stop()
            self.__publishColor(0, 100, 0)
        else:
            self.blinker.stop()
            self.__publishColor(0, 0, 0)

    def __publishColor(self, red, green, blue):
        params = {"key": self.api_key, "red": red, "green": green, "blue": blue}
        response = requests.get(self.url + "/backlight", params=params)
        print(response.json())

    def __publishSoc(self):
        params = {"key": self.api_key, "value": self.soc}
        response = requests.get(self.url + "/set", params=params)
        print(response.json())

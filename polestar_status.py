import logging
from enum import Enum
from os import GRND_RANDOM
from threading import Thread
from time import sleep

import requests
from requests import RequestException


class ChargeState(Enum):
    IDLE = 0
    CHARGING = 1
    CHARGED = 2
    ERROR = 3


BLUE = {
    "red": 0,
    "green": 0,
    "blue": 100
}

RED = {
    "red": 100,
    "green": 0,
    "blue": 0
}

GREEN = {
    "red": 0,
    "green": 100,
    "blue": 0
}

EMPTY = {
    "red": 0,
    "green": 0,
    "blue": 0
}


class Blinker:
    active = False
    on = False
    state = ChargeState.IDLE
    color = EMPTY

    def __init__(self, publisher, delay):
        self.publisher = publisher
        self.delay = delay
        self.thread = Thread(target=self.__loop, daemon=True)
        self.thread.start()

    def start(self, state, color):
        self.active = True
        self.state = state
        self.color = color

    def stop(self):
        self.active = False

    def __loop(self):
        while True:
            sleep(self.delay)
            if not self.active:
                continue
            self.__do_blink()

    def __do_blink(self):
        self.publisher(self.color if self.on else EMPTY)
        self.on = not self.on


class PolestarStatusUpdater:
    state = ChargeState.IDLE
    soc = 0
    blinking = False

    def __init__(self, vu_url, api_key):
        self.url = vu_url
        self.api_key = api_key
        self.blinker = Blinker(publisher=self.__publishColor, delay=2)

    def api_error(self):
        self.blinker.start(self.state, BLUE)

    def publish(self, state, soc):
        self.state = state
        self.soc = soc
        self.__publishSoc()
        logging.info(f"Updating status: {state}, {soc}%" )
        if self.state in [ChargeState.CHARGING, ChargeState.ERROR]:
            self.blinker.start(self.state, GREEN if state == ChargeState.CHARGING else RED)
        elif self.state == ChargeState.CHARGED:
            self.blinker.stop()
            self.__publishColor(GREEN)
        else:
            self.blinker.stop()
            self.__publishColor(EMPTY)

    def __publishColor(self, color):
        params = {"key": self.api_key, **color}
        try:
            response = requests.get(self.url + "/backlight", params=params)
            response.raise_for_status()
            logging.info(response.json())
        except RequestException as e:
            logging.error(e)

    def __publishSoc(self):
        params = {"key": self.api_key, "value": self.soc}
        try:
            response = requests.get(self.url + "/set", params=params)
            response.raise_for_status()
            logging.info(response.json())
        except RequestException as e:
            logging.error(e)

from time import sleep
import logging
import requests
from requests import RequestException

from credentials import ha_api_token, vu1_token
from polestar_status import PolestarStatusUpdater, ChargeState

info = getattr(logging, "INFO", None)
logging.basicConfig(level=info)


def to_charger_state(api_status):
    match api_status:
        case 'Idle' | 'Unspecified' | 'Discharging' | 'Scheduled':
            return ChargeState.IDLE
        case 'Charging' | 'Smart Charging':
            return ChargeState.CHARGING
        case 'Done':
            return ChargeState.CHARGED
        case 'Error' | 'Fault':
            return ChargeState.ERROR
        case _:
            logging.error(f"Unknown charging status: {api_status}")
            return ChargeState.ERROR


def main():
    updater = PolestarStatusUpdater("http://raspberrypi.local:5340/api/v0/dial/130020000650564139323920",
                                    vu1_token)
    while True:
        try:
            soc = query_ha_sensor("sensor.polestar_9155_battery_charge_level")
            charger_state = query_ha_sensor("sensor.polestar_9155_charging_status")
            charger_state = to_charger_state(charger_state.json()["state"])
            updater.publish(charger_state, soc.json()["state"])
        except RequestException as e:
            updater.api_error()
            logging.error(e)
        sleep(10)


def query_ha_sensor(sensor):
    ha_headers = {
        "Authorization": "Bearer " + ha_api_token
    }
    soc = requests.get("http://raspberrypi.local:8123/api/states/" + sensor,
                       headers=ha_headers)
    soc.raise_for_status()
    return soc


if __name__ == "__main__":
    main()

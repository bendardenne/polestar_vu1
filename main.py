from time import sleep
import logging
import requests

from credentials import ha_api_token, vu1_token
from polestar_status import PolestarStatusUpdater, ChargeState


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
            logging.error("Unknown charging status: {}", api_status)
            return ChargeState.ERROR


def main():
    updater = PolestarStatusUpdater("http://raspberrypi.local:5340/api/v0/dial/130020000650564139323920",
                                    vu1_token)
    while True:
        ha_headers = {
            "Authorization": "Bearer " + ha_api_token
        }
        soc = requests.get("http://raspberrypi.local:8123/api/states/sensor.polestar_9155_battery_charge_level",
                           headers=ha_headers).json()

        charger_state = requests.get("http://raspberrypi.local:8123/api/states/sensor.polestar_9155_charging_status",
                                     headers=ha_headers).json()

        charger_state = to_charger_state(charger_state["state"])
        updater.publish(charger_state, soc["state"])
        sleep(10)


if __name__ == "__main__":
    main()

import argparse
import asyncio
import logging
import ssl

import aiohttp
import certifi

from pysveasolar.api import SveaSolarAPI
from pysveasolar.models import BadgesUpdatedMessage
from pysveasolar.token_managers.filesystem import TokenManagerFileSystem

logging.basicConfig(level=logging.DEBUG)


async def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    login_parser = subparsers.add_parser("login")
    login_argument = login_parser.add_argument_group("required arguments")
    login_argument.add_argument(
        "-u", dest="username", help="Username for Svea Solar", required=True
    )
    login_argument.add_argument(
        "-p", dest="password", help="Password for Svea Solar", required=True
    )

    subparsers.add_parser("mydata")
    subparsers.add_parser("user")
    subparsers.add_parser("dashboard")
    subparsers.add_parser("system")

    details = subparsers.add_parser("details")
    details_argument = details.add_argument_group("required arguments")
    details_argument.add_argument(
        "-id", dest="location_id", help="Location Id", required=True
    )

    battery = subparsers.add_parser("battery")
    battery_argument = battery.add_argument_group("required arguments")
    battery_argument.add_argument(
        "-id", dest="battery_id", help="Battery Id", required=True
    )

    websocket = subparsers.add_parser("ws")
    websocket_subparser = websocket.add_subparsers(dest="function", required=True)
    websocket_subparser.add_parser("home")
    ev_websocket = websocket_subparser.add_parser("ev")
    ev_websocket_argument = ev_websocket.add_argument_group("required arguments")
    ev_websocket_argument.add_argument("-id", dest="ev_id", help="EV Id", required=True)

    args = parser.parse_args()

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)

    token_manager = TokenManagerFileSystem()

    async with aiohttp.ClientSession(connector=conn) as session:
        hub = SveaSolarAPI(session, token_manager)
        if args.cmd == "login":
            await hub.async_login(args.username, args.password)
            return

        try:
            token_manager.load()
        except FileNotFoundError:
            print("You have to run the 'login' command first")
            return

        if args.cmd == "mydata":
            response = await hub.async_get_my_data()
            print(f"{response}")
            return

        if args.cmd == "user":
            response = await hub.async_get_user()
            print(f"{response}")
            return

        if args.cmd == "dashboard":
            response = await hub.async_get_dashboard()
            print(f"{response}")
            return

        if args.cmd == "system":
            response = await hub.async_get_my_system()
            print(f"{response}")
            return

        if args.cmd == "details":
            response = await hub.async_get_details(args.location_id)
            print(f"{response}")
            return

        if args.cmd == "battery":
            response = await hub.async_get_battery(args.battery_id)
            print(f"{response}")
            return

        if args.cmd == "ws":
            if args.function == "home":

                def on_keep_alive(msg):
                    print(f"Keep Alive from Home WS: {msg}")

                def on_connected():
                    print("Connected")

                def on_json_data(msg):
                    print(f"Json data received: {msg}")

                def battery_message_handler(msg: BadgesUpdatedMessage):
                    print(f"BadgeUpdate: {msg}")
                    if msg.data.has_battery and msg.data.battery is not None:
                        print(f"Battery name: {msg.data.battery.name}")
                        print(f"Battery status: {msg.data.battery.status}")
                        print(f"Battery SoC: {msg.data.battery.state_of_charge}")
                    if msg.data.has_ev and msg.data.ev is not None:
                        print(f"EV status: {msg.data.ev.status}")

                await hub.async_home_websocket(
                    data_callback=battery_message_handler,
                    connected_callback=on_connected,
                    json_data_callback=on_json_data,
                    keep_alive_callback=on_keep_alive,
                )
                return
            if args.function == "ev":

                def ev_message_handler(msg):
                    print(f"VehicleDetailsUpdated: {msg}")
                    print(f"EV name: {msg.data.name}")
                    print(
                        f"EV charging status: {msg.data.vehicleStatus.chargingStatus}"
                    )
                    print(f"EV battery status: {msg.data.vehicleStatus.batteryLevel}")

                await hub.async_ev_websocket(args.ev_id, ev_message_handler)
                return


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3

# Copyright Claudio Mattera 2019.
# Distributed under the MIT License.
# See accompanying file License.txt, or online at
# https://opensource.org/licenses/MIT


from datetime import datetime
import argparse
import logging
import asyncio
import typing
import os
import re

from tzlocal import get_localzone

import pandas as pd

from pystanley import StanleyAiohttpInterface


FIRST_LINE_PATTERN = re.compile(r".*: crc=(\w\w) (?P<valid>YES|NO)")
SECOND_LINE_PATTERN = re.compile(r".*t=(?P<temperature>-?\d+)")


def main() -> None:
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(async_main())
    finally:
        loop.close()


async def async_main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments.verbose)
    logger = logging.getLogger(__name__)

    password = os.environ["STANLEY_PASSWORD"]

    logger.debug("Removing password from environment")
    del os.environ["STANLEY_PASSWORD"]

    logger.debug("Using Stanley server %s", arguments.url)
    stanley = StanleyAiohttpInterface(
        arguments.url,
        ca_cert=arguments.ca_cert,
        username=arguments.username,
        password=password,
    )

    timezone = get_localzone()

    all_time_series = {
        sensor: pd.Series(
            [read_ds18s20_temperature(sensor)],
            index=pd.to_datetime([datetime.now(timezone)])
        )
        for sensor in arguments.sensor
    }

    for sensor, time_series in all_time_series.items():
        logging.info("Sensor %s: %.2f", sensor, time_series)

    readings = {
        "/sensors/temperature/{}".format(sensor): time_series
        for sensor, time_series in all_time_series.items()
    }

    logging.info("Sending values to Stanley server...")
    await stanley.post_readings(readings)
    logging.info("All done")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record temperature from DS18S20 sensors to Stanley",
        epilog="Stanley password is read from environment variable STANLEY_PASSWORD",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="increase output"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Stanley archiver URL"
    )
    parser.add_argument(
        "--username",
        type=str,
        required=True,
        help="Stanley archiver username"
    )
    parser.add_argument(
        "--ca-cert",
        type=str,
        help="Custom certification authority certificate"
    )
    parser.add_argument(
        "--sensor",
        type=str,
        nargs="+",
        default=list(),
    )

    return parser.parse_args()


def setup_logging(verbose: typing.Optional[int]) -> None:
    if verbose is None or verbose <= 0:
        level = logging.WARN
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        format="%(levelname)s:%(message)s",
        level=level,
    )


def trap_nan(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            return float("nan")
    return inner


@trap_nan
def read_ds18s20_temperature(sensor_id):
    logger = logging.getLogger(__name__)
    filename = "/sys/bus/w1/devices/{}/w1_slave".format(sensor_id)
    with open(filename) as file:
        content = file.read()
        lines = content.split("\n")
        first_line, second_line = lines[0:2]
        first_line_match = FIRST_LINE_PATTERN.match(first_line)
        second_line_match = SECOND_LINE_PATTERN.match(second_line)

        if first_line_match and second_line_match:
            if first_line_match.group("valid") == "YES":
                temperature = float(second_line_match.group("temperature")) / 1000
                logger.info(
                    "Read temperature for sensor %s: %.2f C",
                    sensor_id,
                    temperature,
                )
                return temperature
            else:
                raise RuntimeError("CRC not valid")
        else:
            raise RuntimeError("Output not valid")


if __name__ == "__main__":
    main()

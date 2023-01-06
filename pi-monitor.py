#!/usr/bin/env python3

import sys
import os
import subprocess
import yaml
import configparser
import time
from datetime import datetime, timedelta

from olen.logging.datalogger import DataLogger
from olen.logging.log import Logger
from power_api import SixfabPower, Definition


config_file = os.path.dirname(__file__) + '/pi-monitor.ini'

if not os.path.isfile(config_file):
    print("File {} does not exist".format(config_file))
    sys.exit(1)

config = configparser.ConfigParser(inline_comment_prefixes=';')
config.read([config_file])

logging = Logger(config)
datalogger = DataLogger(config)



def push(var, val):
    logging.debug(var + ": " + str(val))
    datalogger.log('rpi', var.lower().replace(" ", "_"), val)

class RaspberryQmiStatus:
    def __init__(self):
        # self.datalogger = DataLoggerMqtt()
        self._serving_system = None
        self._packet_stats = None
        self._signal_info = None
        self._serving_system_tz = None
        self._packet_stats_tz = None
        self._signal_info_tz = None

    def qmiget(self, command):
        y = None
        try:
            out = subprocess.run(["/usr/bin/sudo","/usr/bin/qmicli", "-d", "/dev/cdc-wdm0", "-p", command], stdout=subprocess.PIPE)
            res = out.stdout.decode('utf-8').replace("\t", "    ").replace("[0]:", "-")
            res = res.replace("[/dev/cdc-wdm0] ", "")
            res = res.replace("[Invalid UTF-8]", "")
            res = res.replace("     ", "    ")
            res = res.replace("minutes", "")
            res = res.replace("hours", "")
            res = res.replace("'1'", "")
            res = res.replace("'off' (lte)", "'off'")
            res = res.replace("'on' (lte)", "'on'")
            res = res.replace("Successfully got signal strength", "")
            res = res.replace("Successfully got signal info", "")
            res = res.replace("Network 'lte'", "Network")
            # print(res)
            y = yaml.load(res,  Loader=yaml.FullLoader)
        except Exception as e:
            logging.error(e)
            pass
        logging.debug(y)
        return y

    @property
    def serving_system(self):
        if not self._serving_system_tz or self._serving_system_tz < datetime.now() - timedelta(minutes=1):
            getit =  self.qmiget("--nas-get-serving-system")
            if getit:
                self._serving_system = getit
                self._serving_system_tz = datetime.now()
        print(self._serving_system)
        return self._serving_system

    @property
    def packet_stats(self):
        if not self._packet_stats_tz or self._packet_stats_tz < datetime.now() - timedelta(minutes=1):
            getit = self.qmiget("--wds-get-packet-statistics")
            if getit:
                self._packet_stats = getit
                self._packet_stats_tz = datetime.now()
        return self._packet_stats

    @property
    def signal_info(self):
        if not self._signal_info_tz or self._signal_info_tz < datetime.now() - timedelta(minutes=1):
            getit = self.qmiget("--nas-get-signal-info")
            if getit:
                self._signal_info = getit
                self._signal_info_tz = datetime.now()
        return self._signal_info

    @property
    def connection_type(self):
        if self.signal_info:
            return list(self.signal_info.keys())[0]
        return None

    @property
    def connection_data(self):
        if self.signal_info and self.connection_type:
            return self.signal_info[self.connection_type]
        return None

    @property
    def roaming(self):
        if self.serving_system:
            return self.serving_system['Successfully got serving system']['Roaming status']
        return None

    @property
    def xgpp_location(self):
        if self.serving_system:
            return self.serving_system['Successfully got serving system']['3GPP location area code']
        return None

    @property
    def xgpp_cell_id(self):
        if self.serving_system:
            return self.serving_system['Successfully got serving system']['3GPP cell ID']
        return None


    @property
    def rssi(self):
        if self.connection_data:
            return self.connection_data['RSSI'].split(" ")[0]
        return None

    @property
    def snr(self):
        if self.connection_data:
            return self.connection_data['SNR'].split(" ")[0]



class RaspberryPowerStatus:
    def __init__(self):
        self.api = SixfabPower()
        self._input_temperature = None
        self._input_voltage = None
        self._input_current = None
        self._input_power = None
        self._battery_temperature = None
        self._battery_voltage = None
        self._battery_current = None
        self._battery_power = None
        self._battery_level = None
        self._battery_health = None
        self._system_temperature = None
        self._system_voltage = None
        self._system_current = None
        self._system_power = None
        self._fan_health = None
        self._fan_speed = None

    @property
    def input_temperature(self):
        try:
            getit = self.api.get_input_temp()
            if getit:
                self._input_temperature = getit
            else:
                self._input_temperature = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._input_temperature

    @property
    def input_voltage(self):
        try:
            getit = self.api.get_input_voltage()
            if getit:
                self._input_voltage = getit
            else:
                self._input_voltage = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._input_voltage

    @property
    def input_current(self):
        try:
            getit = self.api.get_input_current()
            if getit:
                self._input_current = getit
            else:
                self._input_current = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._input_current

    @property
    def input_power(self):
        try:
            getit = self.api.get_input_power()
            if getit:
                self._input_power = getit
            else:
                self._input_power = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._input_power

    @property
    def battery_temperature(self):
        try:
            getit = self.api.get_battery_temp()
            if getit:
                self._battery_temperature = getit
            else:
                self._battery_temperature = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._battery_temperature

    @property
    def battery_voltage(self):
        try:
            getit = self.api.get_battery_voltage()
            if getit:
                self._battery_voltage = getit
            else:
                self._battery_voltage = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._battery_voltage

    @property
    def battery_power(self):
        try:
            getit = self.api.get_battery_power()
            if getit:
                self._battery_power = getit
            else:
                self._battery_power = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._battery_power

    @property
    def battery_current(self):
        try:
            getit = self.api.get_battery_current()
            if getit:
                self._battery_current = getit
            else:
                self._battery_current = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._battery_current

    @property
    def battery_level(self):
        try:
            getit = self.api.get_battery_level()
            if getit:
                self._battery_level = getit
            else:
                self._battery_level = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._battery_level

    @property
    def battery_health(self):
        try:
            getit = self.api.get_battery_health()
            if getit:
                self._battery_health = getit
            else:
                self._battery_health = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._battery_health


    @property
    def system_temperature(self):
        try:
            getit = self.api.get_system_temp()
            if getit:
                self._system_temperature = getit
            else:
                self._system_temperature = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._system_temperature

    @property
    def system_voltage(self):
        try:
            getit = self.api.get_system_voltage()
            if getit:
                self._system_voltage = getit
            else:
                self._system_voltage = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._system_voltage

    @property
    def system_power(self):
        try:
            getit = self.api.get_system_power()
            if getit:
                self._system_power = getit
            else:
                self._system_power = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._system_power

    @property
    def system_current(self):
        try:
            getit = self.api.get_system_current()
            if getit:
                self._system_current = getit
            else:
                self._system_current = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._system_current

    @property
    def fan_health(self):
        try:
            getit = self.api.get_fan_health()
            if getit:
                self._fan_health = getit
            else:
                self._fan_health = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._fan_health

    @property
    def fan_speed(self):
        try:
            getit = self.api.get_fan_speed()
            if getit:
                self._fan_speed = getit
            else:
                self._fan_speed = 0
        except Exception as e:
            logging.error(e)
            pass
        return self._fan_speed








"""
logging.error("Battery Temp: " + str(api.get_battery_temp()))
logging.error("Battery Voltage: " + str(api.get_battery_current()))
logging.error("Battery Current: " + str(api.get_battery_current()))
logging.error("Battery Power: " + str(api.get_battery_power()))
logging.error("Battery Level: " + str(api.get_battery_level()))
logging.error("Battery Health: " + str(api.get_battery_health()))
"""


QMI = RaspberryQmiStatus()
Power = RaspberryPowerStatus()

i = 0
while True:

    if i == 0:
        # logging.error("************* QMI Data **************")
        push('Connection', QMI.connection_type)
        push('Roaming', QMI.roaming)
        push('3GPP Location', QMI.xgpp_location)
        push('3GPP Cell ID', QMI.xgpp_cell_id)
        push('RSSI_dbm', QMI.rssi)
        push('SNR_db', QMI.snr)


    # logging.error("************* Input Sensors **************")
    push("Input Temperature", Power.input_temperature)
    push("Input Voltage", Power.input_current)
    push("Input Current", Power.input_current)
    push("Input Power", Power.input_power)
    push("System Temperature", Power.system_temperature)
    push("System Voltage", Power.system_current)
    push("System Current", Power.system_current)
    push("System Power", Power.system_power)
    push("Battery Temperature", Power.battery_temperature)
    push("Battery Voltage", Power.battery_voltage)
    push("Battery Current", Power.battery_current)
    push("battery Power", Power.battery_power)
    push("battery SOC", Power.battery_level)
    push("battery Health", Power.battery_health)
    push("Fan health", Power.fan_health)
    push("Fan Speed", Power.fan_speed)
    i = i + 1
    if i == 10:
        i = 0
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Exiting due to user interrupt")
        sys.exit(0)
    except Exception as e:
        logging.error(e)
        pass


sys.exit()

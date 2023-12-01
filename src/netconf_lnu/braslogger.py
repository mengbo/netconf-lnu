from .netconf import Netconf
import configparser
import json
import socket
import time


class BRASLogger:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.devices = {}
        self.syslog = {}
        self.load_config()

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_file_path)

        for section_name in config.sections():
            if section_name.startswith("device."):
                device_name = section_name[len("device."):]
                section_config = {}
                for key, value in config.items(section_name):
                    try:
                        section_config[key] = json.loads(value)
                    except json.JSONDecodeError:
                        section_config[key] = value
                self.devices[device_name] = \
                    Netconf.create_netconf_instance(section_config)
            elif section_name == "syslog":
                for key, value in config.items(section_name):
                    self.syslog[key] = value
        return self


    def send_syslog_message(self, message):
        # logger -p local6.info -n 10.10.10.10 -P 514 "hello"
        syslog_server_ip = self.syslog['server']
        syslog_server_port = int(self.syslog['port'])

        priority = "<182>"
        version = "1"
        appname = "netconf-lnu"
        log_message = f"{priority}{version} {appname}: {message}"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(log_message.encode(), (syslog_server_ip, syslog_server_port))
        sock.close()


    def get_addr_tab(self):
        addr_tab = []
        for dev_name, dev_instance in self.devices.items():
            addr_tab.extend(dev_instance.get_addr_tab())
        return addr_tab


    def write_syslog(self):
        self.send_syslog_message("BRAS address table start")
        for addr in self.get_addr_tab():
            self.send_syslog_message(f"{addr['MAC']} {addr['IPv4']} {addr['IPv6']}")
        time.sleep(10)
        self.send_syslog_message("BRAS address table end")

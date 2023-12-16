from .braslogger import BRASLogger
import pprint
import logging

#logging.basicConfig(level=logging.DEBUG)

def print_addr_tab(bras_logger):
    pp = pprint.PrettyPrinter(indent=2)
    for dev_name, dev_instance in bras_logger.devices.items():
        pp.pprint(dev_instance.get_user_info())
        pp.pprint(dev_instance.get_nd_table())
        pp.pprint(dev_instance.get_addr_tab(auth=True))


def download_schema(bras_logger):
    csbras_netconf = bras_logger.devices['csbras']
    dybras_netconf = bras_logger.devices['dybras']

    csbras_netconf.download_schema_list("./schema", "csbras.xml")
    dybras_netconf.download_schema_list("./schema", "dybras.xml")

    csbras_netconf.download_yang("./schema",
                                 "H3C-nd-data", 
                                "2020-01-11"
                                 )
    csbras_netconf.download_yang("./schema",
                                 "H3C-bras-data", 
                                 "2020-01-11"
                                 )
    dybras_netconf.download_yang("./schema",
                                 "huawei-ipv6-nd", 
                                 "2021-02-02"
                                 )
    dybras_netconf.download_yang("./schema",
                                 "huawei-bras-user-manage", 
                                 "2020-04-27"
                                 )


def get_running_config_test(bras_logger):
    csbras_netconf = bras_logger.devices['csbras']
    print(csbras_netconf.get_all_running_config())

    dybras_netconf = bras_logger.devices['dybras']
    filter = """
    <filter type="subtree">
      <ifm:ifm xmlns:ifm="urn:huawei:yang:huawei-ifm">
        <ifm:interfaces>
          <ifm:interface/>
        </ifm:interfaces>
      </ifm:ifm>
    </filter>
    """
    print(dybras_netconf.get_running_config(filter))


def dispatch_test(bras_logger): 
    #csbras_netconf = bras_logger.devices['csbras']
    dybras_netconf = bras_logger.devices['dybras']
    
    namespace = "urn:huawei:yang:huawei-bras-user-manage"
    payload = """
    <filter-access-tables xmlns="{ns}">
      <ip-pool-name>ipoe</ip-pool-name>
    </filter-access-tables>
    """.format(ns=namespace)
    
    print(dybras_netconf.dispatch(payload))


def netconf_test(bras_logger): 
    #csbras_netconf = bras_logger.devices['csbras']
    dybras_netconf = bras_logger.devices['dybras']

    namespace = "urn:huawei:yang:huawei-bras-user-manage"
    filter = """
    <bras-user-manage xmlns="{ns}">
    </bras-user-manage>
    """.format(ns=namespace)
     
    print(dybras_netconf.get(filter))


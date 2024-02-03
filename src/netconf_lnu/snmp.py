from pysnmp.hlapi import *
import ipaddress

class HuaweiSNMP:
    def __init__(self, community, ip_address):
        self.community = community
        self.ip_address = ip_address

    def get_addr_tab(self):
        mac_addr_tab = self.get_access_mac()
        ipv4_addr_tab = self.get_access_ipv4()
        ipv6_addr_tab = self.get_access_ipv6()

        common_keys = \
            set(mac_addr_tab.keys()) & \
            set(ipv4_addr_tab.keys()) & \
            set(ipv6_addr_tab.keys())

        addr_tab = []
        for key in common_keys:
            if not ipv4_addr_tab[key].startswith('10.'):
                continue
            if not ipv6_addr_tab[key].startswith('2001:'):
                continue
            addr_tab.append({
                'MAC': mac_addr_tab[key],
                'IPv4': ipv4_addr_tab[key],
                'IPv6': ipv6_addr_tab[key]
            })
        return addr_tab
       
    def get_access_mac(self):
        oid_mac = '1.3.6.1.4.1.2011.5.2.1.15.1.17'
        return self.snmp_walk(oid_mac, self.hex_string_to_mac)

    def get_access_ipv4(self):
        oid_ipv4 = '1.3.6.1.4.1.2011.5.2.1.15.1.15'
        return self.snmp_walk(oid_ipv4, self.hex_string_to_ipv4)

    def get_access_ipv6(self):
        oid_ipv6 = '1.3.6.1.4.1.2011.5.2.1.15.1.60'
        return self.snmp_walk(oid_ipv6, self.hex_string_to_ipv6)

    def hex_string_to_mac(self, hex_string):
        try:
            return ':'.join([hex_string[i:i+2] for i in range(2, len(hex_string), 2)])
        except ValueError as e:
            print(f"Error converting Hex-STRING to MAC: {e}")
            return None

    def hex_string_to_ipv4(self, hex_string):
        try:
            return str(ipaddress.IPv4Address(hex_string))
        except ValueError as e:
            print(f"Error converting Hex-STRING to IPv4: {e}")
            return None

    def hex_string_to_ipv6(self, hex_string):
        try:
            byte_array = bytes.fromhex(hex_string[2:])
            ipv6_address = ipaddress.IPv6Address(byte_array)
            return str(ipv6_address)
        except ValueError as e:
            print(f"Error converting Hex-STRING to IPv6: {e}")
            return None

    def snmp_walk(self, oid, conversion_function):
        iterator = nextCmd(
            SnmpEngine(),
            CommunityData(self.community),
            UdpTransportTarget((self.ip_address, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False
        )

        result = {}
        for (errorIndication, errorStatus, errorIndex, varBinds) in iterator:
            if errorIndication:
                print(f"SNMP Walk failed: {errorIndication}")
                break
            elif errorStatus:
                print(f"SNMP Walk failed: {errorStatus}")
                break
            else:
                for varBind in varBinds:
                    oid_str = str(varBind[0])
                    hex_string = varBind[1].prettyPrint()

                    oid_part = oid_str.split('.')[-1]
                    conv_str = conversion_function(hex_string)

                    result[oid_part] = conv_str
        return result

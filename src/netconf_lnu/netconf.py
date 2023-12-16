from ncclient import manager
import xml.dom.minidom
import xmltodict
from lxml import etree
import re
import os


class Netconf:
    def __init__(self, dev_info):
        self.conn = manager.connect(**dev_info, hostkey_verify=False,
                                    allow_agent=False, look_for_keys=False)

    @staticmethod
    def create_netconf_instance(dev_info):
        device_name = dev_info.get('device_params', {}).get('name', '').lower()
        if device_name == 'h3c':
            return H3CNetconf(dev_info)
        elif device_name == 'huaweiyang':
            return HuaweiNetconf(dev_info)
        else:
            raise ValueError(f"Unsupported device type: {device_name}")

    def dispatch(self, payload):
        reply = self.conn.dispatch(etree.fromstring(payload)).xml
        xml_with_blank_lines = xml.dom.minidom.parseString(reply).toprettyxml(
            indent='  ')
        return re.sub(r'\n\s*\n', '\n', xml_with_blank_lines)

    def get(self, filter):
        reply = self.conn.get(('subtree', filter)).data_xml
        xml_with_blank_lines = xml.dom.minidom.parseString(reply).toprettyxml(
            indent='  ')
        return re.sub(r'\n\s*\n', '\n', xml_with_blank_lines)

    def get_all_running_config(self):
        reply = self.conn.get_config(source='running').data_xml
        xml_with_blank_lines = xml.dom.minidom.parseString(reply).toprettyxml(
            indent='  ')
        return re.sub(r'\n\s*\n', '\n', xml_with_blank_lines)

    def get_running_config(self, filter):
        reply = self.conn.get_config('running', filter).data_xml
        xml_with_blank_lines = xml.dom.minidom.parseString(reply).toprettyxml(
            indent='  ')
        return re.sub(r'\n\s*\n', '\n', xml_with_blank_lines)

    def get_schema_list(self):
        namespace = "urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"
        netconf_state = """
        <netconf-state xmlns="{ns}">
          <schemas/>
        </netconf-state>
        """.format(ns=namespace)
        return self.get(netconf_state)

    def download_schema_list(self, schema_dir, filename):
        os.makedirs(schema_dir, exist_ok=True)
        with open(os.path.join(schema_dir, filename), 'w') as file:
            file.write(self.get_schema_list())

    def get_schema(self, identifier, version):
        reply = self.conn.get_schema(identifier, version).data
        return reply.replace("\r\n", "\n") 

    def download_yang(self, schema_dir, identifier, version):
        os.makedirs(schema_dir, exist_ok=True)
        with open(os.path.join(schema_dir, identifier + '.yang'), 'w') as file:
            file.write(self.get_schema(identifier, version))

    def get_addr_tab_noauth(self, user_mac_key, nd_mac_key, ipv4_key, ipv6_key):
        user_info = {}
        for user in self.get_user_info():
            if user_mac_key not in user or ipv4_key not in user:
                continue
            if not user[ipv4_key].startswith('10.'):
                continue
            user_info[user[user_mac_key]] = user[ipv4_key]
        nd_talbe = {}
        for nd in self.get_nd_table():
            if not nd[ipv6_key].startswith('2001:'):
                continue
            if nd[nd_mac_key] not in nd_talbe:
                nd_talbe[nd[nd_mac_key]] = []
            nd_talbe[nd[nd_mac_key]].append(nd[ipv6_key])
        macs = set(user_info.keys()) & set(nd_talbe.keys())
        addr_tab = []
        for mac in macs:
            for ipv6 in nd_talbe[mac]:
                addr_tab.append({
                    'MAC': mac,
                    'IPv4': user_info[mac],
                    'IPv6': ipv6
                })
        return addr_tab

    def get_addr_tab_auth(self, mac_key, ipv4_key, ipv6_key):
        addr_tab = []
        for user in self.get_user_info():
            if mac_key not in user or ipv4_key not in user or ipv6_key not in user:
                continue
            if not user[ipv4_key].startswith('10.'):
                continue
            if not user[ipv6_key].startswith('2001:'):
                continue
            addr_tab.append({
                'MAC': user[mac_key],
                'IPv4': user[ipv4_key],
                'IPv6': user[ipv6_key]
            })
        return addr_tab


class H3CNetconf(Netconf):
    def get_user_info(self):
        namespace = "http://www.h3c.com/netconf/data:1.0-BRAS"
        filter = """
        <BRAS xmlns="{ns}">
          <AccessUserInfo>
            <UserInfo>
              <UserID></UserID>
              <UserName></UserName>
              <AuthType></AuthType>
              <MacAddr></MacAddr>
              <IpAddr></IpAddr>
              <IPv6Addr></IPv6Addr>
            </UserInfo>
          </AccessUserInfo>
        </BRAS>
        """.format(ns=namespace)
        reply = self.conn.get(('subtree', filter)).data_xml
        data = xmltodict.parse(reply)
        list = data['data']['BRAS']['AccessUserInfo']['UserInfo']
        return list

    def get_nd_table(self):
        namespace = "http://www.h3c.com/netconf/data:1.0-ND"
        filter = """
        <ND xmlns="{ns}">
          <NDTable>
            <NDEntry>
              <IfIndex></IfIndex>
              <Ipv6Address></Ipv6Address>
              <MacAddress></MacAddress>
              <VLANID></VLANID>
              <Type></Type>
              <State></State>
            </NDEntry>
          </NDTable>
        </ND>
        """.format(ns=namespace)
        reply = self.conn.get(('subtree', filter)).data_xml
        data = xmltodict.parse(reply)
        list = data['data']['ND']['NDTable']['NDEntry']
        return list

    def get_addr_tab(self, auth=True):
        if auth:
            return super().get_addr_tab_auth(
                'MacAddr', 'IpAddr', 'IPv6Addr')
        else:
            return super().get_addr_tab_noauth(
                'MacAddr', 'MacAddress', 'IpAddr', 'Ipv6Address')


class HuaweiNetconf(Netconf):
    def get_user_info(self):
        namespace = "urn:huawei:yang:huawei-bras-user-manage"
        filter = """
        <bras-user-manage xmlns="{ns}">
          <access-tables>
            <access-table>
              <access-user-basic-info>
                <access-user-name></access-user-name>
                <access-ipaddress></access-ipaddress>
                <access-mac-address></access-mac-address>
                <ipv6-addr></ipv6-addr>
              </access-user-basic-info>
            </access-table>
          </access-tables>
        </bras-user-manage>
        """.format(ns=namespace)
        reply = self.conn.get(('subtree', filter)).data_xml
        data = xmltodict.parse(reply)
        access_table_list = data['data']['bras-user-manage']\
            ['access-tables']['access-table']
        list = [entry['access-user-basic-info'] for entry in access_table_list]
        return list

    def get_nd_table(self):
        namespace = "urn:huawei:yang:huawei-ipv6-nd"
        filter = """
        <ipv6-nd xmlns="{ns}">
          <ipv6-neighbors>
            <ipv6-neighbor>
              <ipv6-addr></ipv6-addr>
              <mac-addr></mac-addr>
              <vlan-id></vlan-id>
              <state></state>
              <static-flag></static-flag>
            </ipv6-neighbor>
          </ipv6-neighbors>
        </ipv6-nd>
        """.format(ns=namespace)
        reply = self.conn.get(('subtree', filter)).data_xml
        data = xmltodict.parse(reply)
        list = data['data']['ipv6-nd']['ipv6-neighbors']['ipv6-neighbor']
        if isinstance(list, dict):
            list = [list]
        return list

    def get_addr_tab(self, auth=True):
        if auth:
            return super().get_addr_tab_auth(
                'access-mac-address', 'access-ipaddress', 'ipv6-addr')
        else:
            return super().get_addr_tab_noauth(
                'access-mac-address', 'mac-addr', 'access-ipaddress', 'ipv6-addr')

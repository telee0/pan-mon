"""

pan-os_mon v1.0 [20260627]

Script to monitor PAN-OS device over API

by Terence LEE <telee.hk@gmail.com>

https://github.com/telee0/pan-os_mon

"""

import json
import requests
import urllib3
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


class PanAPI:

    def __init__(self, cf: dict):
        self.verbose = cf['verbose']
        self.debug = cf['debug']

        self.host = cf['hostname']
        self.user = cf['username']
        self.password = cf['password']
        self.api_key = self.keygen()

        self.session = requests.Session()

    def keygen(self):
        urllib3.disable_warnings()
        url = f"https://{self.host}/api/?type=keygen"

        try:
            response = requests.post(
                url,
                data={'user': self.user, 'password': self.password},
                verify=False,
                timeout=5,
            )
            if self.verbose:
                print("pan_api: response: ", response.text)
        except Exception as e:
            if self.verbose:
                print("pan_api: {0}: {1}".format(self.host, e))
            return ""

        result = ET.fromstring(response.content)
        api_key = result.find('result/key')

        return api_key.text if api_key is not None else ""

    def op(self, cmd: str) -> ET.Element:

        r = self.session.get(
            f'https://{self.host}/api/',
            params={
                'type': 'op',
                'cmd': cmd,
                'key': self.api_key,
            },
            verify=False,
            timeout=5,
        )

        r.raise_for_status()

        root = ET.fromstring(r.text)

        if root.attrib.get('status') != 'success':
            raise RuntimeError(r.text)

        return root

    def show_run_res_mon(self) -> dict[str, float]:
        cmd = '''
        <show><running><resource-monitor>
        <second><last>5</last></second>
        </resource-monitor></running></show>
        '''
        start_time = datetime.now()
        root = self.op(cmd)
        end_time = datetime.now()

        # print(ET.tostring(root, encoding='unicode'))

        result = {'dp': {}}

        dp_list = root.find('./result/resource-monitor/data-processors')
        if dp_list is None:
            return result

        struct = {
            'cpu-load-average': ('coreid', 'value'),
            'cpu-load-maximum': ('coreid', 'value'),
            'resource-utilization': ('name', 'value'),
        }

        for dp in dp_list:
            second = dp.find('second')
            if second is None:
                continue
            task = second.find('task')
            if task is None:
                continue
            data = {}
            for item in task:
                data[item.tag] = int(item.text.rstrip('%'))
            for section, (name, value) in struct.items():
                res = second.find(section)
                if res is None:
                    continue
                data[section] = {}
                for entry in res.findall('entry'):
                    key = entry.findtext(name)
                    values = [int(v) for v in entry.findtext(value).split(',')]
                    data[section][key] = values
            result['dp'][dp.tag] = data

        result['time_stamp'] = start_time  # - timedelta(seconds=1)
        result['start_time'] = start_time.isoformat()
        result['end_time'] = end_time.isoformat()
        result['elapsed_seconds'] = (end_time - start_time).total_seconds()

        # print(json.dumps(result, indent=2))

        return result
        # raise NotImplementedError()


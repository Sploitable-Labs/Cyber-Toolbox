import json
import platform
import os
import wmi # python -m pip install wmi pywin32

from pprint import pprint as pp

def win_enum():

    results = dict()
    results['platform'] = {}
    results['platform']['system'] = platform.uname().system
    results['platform']['node'] = platform.uname().node
    results['platform']['release'] = platform.uname().release
    results['platform']['version'] = platform.uname().version
    results['platform']['architecture'] = platform.uname().machine
    results['platform']['processor'] = platform.uname().processor
    results['current_user'] = os.getlogin()
    results['env'] = {}
    for env in os.environ:
        results['env'][env] = os.getenv(env)

    # WMI

    wmi_conn = wmi.WMI()
    results['wmi'] = {}

    # Get running processes
    results['wmi']['processes'] = {}
    for process in wmi_conn.Win32_Process():
        results['wmi']['processes'][process.ProcessID] = process.Name

    # Get services
    results['wmi']['services'] = {}
    for service in wmi_conn.Win32_Service():
        results['wmi']['services'][service.Name] = {
            'state': service.State,
            'start_mode': service.StartMode,
            'display_name': service.DisplayName
        }

    # Get users and groups
    results['wmi']['groups'] = {}
    for group in wmi_conn.Win32_Group():
        results['wmi']['groups'][group.Caption] = []
        for user in group.associators(wmi_result_class="Win32_UserAccount"):
            results['wmi']['groups'][group.Caption].append(user.Caption)

    # Get network interfaces
    results['wmi']['network_interfaces'] = {}
    for interface in wmi_conn.Win32_NetworkAdapterConfiguration(IPEnabled=1):
        results['wmi']['network_interfaces'][interface.Description] = {
            'mac': interface.MACAddress,
            'IPs': [ip for ip in interface.IPAddress]
        }

    # Get programs that start on boot
    results['wmi']['start_on_boot'] = {}
    for program in wmi_conn.Win32_StartupCommand():
        results['wmi']['start_on_boot'][program.Caption] = {
            'command': program.Command,
            'location': program.Location
        }

    # Get shares
    results['wmi']['shares'] = {}
    for share in wmi_conn.Win32_Share():
        results['wmi']['shares'][share.Name] = share.Path


    with open("./data/win_enum.txt", 'w') as ofile:
        json_results = json.dumps(results)
        ofile.write(json_results)


if __name__ == "__main__":
    win_enum()

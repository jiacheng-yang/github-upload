import csv
import json

import requests
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from zeep import Client
from zeep.cache import SqliteCache
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport

disable_warnings(InsecureRequestWarning)
username = 'ucmadmin'
password = 'N!ke360#^)'
host = '10.82.60.196'

wsdl = 'file://D:/nike UC/Automation/axlsqltoolkit/schema/current/AXLAPI.wsdl'
server = 'https://{host}:8443/axl/'.format(host=host)
binding = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"

session = Session()
session.verify = False
session.auth = HTTPBasicAuth(username, password)

transport = Transport(cache=SqliteCache(), session=session, timeout=20)
history = HistoryPlugin()
client = Client(wsdl=wsdl, transport=transport, plugins=[history])
service = client.create_service(binding, server)


def show_history():
    for item in [history.last_sent, history.last_received]:
        print(etree.tostring(item["envelope"], encoding="unicode", pretty_print=True))


def show_license(request):
    return render(request, 'plm.html',
                  {'rows': sync_license(), 'data_available': license_data()[0], 'data_installed': license_data()[1],
                   'data_required': license_data()[2]})


def PLMInfo():
    with client.settings(strict=False):
        response = service.getSmartLicenseStatus()
        # print(response)

    lic = response['LicenseDetails']['LicenseStatus']
    lic_usage = lic['Entitlement']
    CUWL_usage = lic_usage[0]['Count']
    EHNP_usage = lic_usage[1]['Count']
    EHN_usage = lic_usage[2]['Count']
    Basic_usage = lic_usage[3]['Count']
    Ess_usage = lic_usage[4]['Count']
    return CUWL_usage, EHNP_usage, EHN_usage, Basic_usage, Ess_usage


def filter_license():
    plm = PLMInfo()
    requests.packages.urllib3.disable_warnings()
    lic1 = ('UCM_CUWLStandard', -plm[0], 8414, 8414 - plm[0])
    lic2 = ('UCM_EnhancedPlus', -plm[1], 18, 18 - plm[1])
    lic3 = ('UCM_Enhanced', -plm[2], 474, 474 - plm[2])
    lic4 = ('UCM_Basic', -plm[3], 0, 0 - plm[3])
    lic5 = ('UCM_Essential', -plm[4], 140, 140 - plm[4])
    lic6 = ('Total', -(plm[0] + plm[1] + plm[2] + plm[3] + plm[4]), 9046, 9046 - plm[0] - plm[1] - plm[2] - plm[3] - plm[4])
    header = ['Name', 'In_Use', 'Purchased', 'Balance']
    with open('licenses.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(lic1)
        writer.writerow(lic2)
        writer.writerow(lic3)
        writer.writerow(lic4)
        writer.writerow(lic5)
        writer.writerow(lic6)


def license_data():
    filter_license()
    with open('licenses.csv', 'r', encoding='utf-8', newline='') as csvfile1:
        reader1 = csv.DictReader(csvfile1)
        available = [row['Balance'] for row in reader1]
    with open('licenses.csv', 'r', encoding='utf-8', newline='') as csvfile2:
        reader2 = csv.DictReader(csvfile2)
        required = [row['In_Use'] for row in reader2]
    with open('licenses.csv', 'r', encoding='utf-8', newline='') as csvfile3:
        reader3 = csv.DictReader(csvfile3)
        installed = [row['Purchased'] for row in reader3]
    data_available = json.dumps(available)
    data_required = json.dumps(required)
    data_installed = json.dumps(installed)
    return data_available, data_installed, data_required


def sync_license():
    filter_license()
    with open('licenses.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = [row for row in reader]
        return rows


def remove_phone(request):
    result = ''
    if request.is_ajax() and request.method == 'POST':
        try:
            phone_exist = service.listPhone(searchCriteria={'securityProfileName': 'Cisco Unified Client Services '
                                                                                   'Framework - Standard SIP '
                                                                                   'Non-Secure Profile'},
                                            returnedTags={'name': '', 'ownerUserName': ''})
            phones = phone_exist['return']['phone']

            quantity = 0

            for phone in phones:
                phone_name = phone.name
                if phone.ownerUserName['_value_1'] is None:
                    userID = phone_name[3:]
                    print(userID)

                    # delete CSF
                    try:
                        phone_delete = service.removePhone(name=phone_name)
                        print(phone_delete)
                    except Fault:
                        show_history()

                    # delete TCT
                    TCT_name = 'TCT' + userID
                    TCT_exist = service.listPhone(searchCriteria={'name': TCT_name},
                                                  returnedTags={'name': ''})
                    if TCT_exist['return'] is not None:
                        TCT_delete = service.removePhone(name=TCT_name)
                        print(TCT_delete)

                    # delete TAB
                    TAB_name = 'TAB' + userID
                    TAB_exist = service.listPhone(searchCriteria={'name': TAB_name},
                                                  returnedTags={'name': ''})
                    if TAB_exist['return'] is not None:
                        TAB_delete = service.removePhone(name=TAB_name)
                        print(TAB_delete)

                    # delete BOT
                    BOT_name = 'BOT' + userID
                    BOT_exist = service.listPhone(searchCriteria={'name': BOT_name},
                                                  returnedTags={'name': ''})
                    if BOT_exist['return'] is not None:
                        BOT_delete = service.removePhone(name=BOT_name)
                        print(BOT_delete)

                    # delete UDP
                    udp_name1 = 'UDP-8841-' + userID
                    udp_exist1 = service.listDeviceProfile(searchCriteria={'name': udp_name1},
                                                           returnedTags={'name': ''})
                    udp_name2 = 'UDP-8845-' + userID
                    udp_exist2 = service.listDeviceProfile(searchCriteria={'name': udp_name2},
                                                           returnedTags={'name': ''})
                    udp_name3 = 'UDP-8945-' + userID
                    udp_exist3 = service.listDeviceProfile(searchCriteria={'name': udp_name3},
                                                           returnedTags={'name': ''})
                    udp_name4 = 'UDP-9951-' + userID
                    udp_exist4 = service.listDeviceProfile(searchCriteria={'name': udp_name4},
                                                           returnedTags={'name': ''})
                    if udp_exist1['return'] is not None:
                        UDP_delete = service.removeDeviceProfile(name=udp_name1)
                    elif udp_exist2['return'] is not None:
                        UDP_delete = service.removeDeviceProfile(name=udp_name2)
                    elif udp_exist3['return'] is not None:
                        UDP_delete = service.removeDeviceProfile(name=udp_name3)
                    elif udp_exist4['return'] is not None:
                        UDP_delete = service.removeDeviceProfile(name=udp_name4)
                    else:
                        UDP_delete = "NO UDP"
                    print(UDP_delete)

                    # delete FAC
                    fac_exist = service.listFacInfo(searchCriteria={'name': userID},
                                                    returnedTags={'name': ''})
                    if fac_exist['return'] is not None:
                        FAC_delete = service.removeFacInfo(name=userID)
                        print(FAC_delete)
                    result = 'remove successfully <br>'
                    quantity += 1
            result = result + 'Remove ' + str(quantity) + ' users'
            print(quantity)
        except Fault:
            show_history()
    return JsonResponse(result, safe=False)


def DownLoadApiView(request):
    """
        API文档下载
    :param request:
    :return:
    """
    if request.method == "GET":
        file = open('licenses.csv', 'rb')
        response = HttpResponse(file)
        response['Content-Type'] = 'application/octet-stream'  # 设置头信息，告诉浏览器这是个文件
        response['Content-Disposition'] = 'attachment;filename="licenses.csv"'
        return response


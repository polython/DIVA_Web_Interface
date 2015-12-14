import http.client
import xml.etree.ElementTree as ET
import time


# need session code, request ID as arguments
def get_req_status(skey, rid):

    sessionkey = str(skey)
    reqid = str(rid)

    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\">\r\n" \
              "<env:Body>\r\n<p:getRequestInfo xmlns:p=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xs:sessionCode xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + sessionkey + "</xs:sessionCode>\r\n    " \
              "<xs:requestNumber xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" \
              + reqid + "</xs:requestNumber>\r\n</p:getRequestInfo>\r\n" \
              "</env:Body>\r\n</env:Envelope>"

    headers = {
        'accept': "application/xml",
        'content-type': "text/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/getRequestInfo", payload, headers)

    res = conn.getresponse()
    data = res.read()

    root = ET.fromstring(data.decode('UTF8'))
    divareqstat = root[0][0].text

    if int(divareqstat) != 1000:
        return 3
    else:
        progress = root[0][1][4].text

    return int(progress)


# check if request is completed
def check_stat_comp(key, id_):
    if get_req_status(key, id_) == -1:
        print("Request failed, please verify a tape is inserted")
        return -1
    elif get_req_status(key, id_) == 3:
        print("No such request")
        return -2
    elif get_req_status(key, id_) != 100:
        return -3
    else:
        print("Request complete, tape has been re-imported")
        return 100


if __name__ == '__main__':
    check_stat_comp("b45b0201-0afb-4943-86e3-0d4148679530", 3023)





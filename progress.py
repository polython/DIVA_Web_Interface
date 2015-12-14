import http.client
import xml.etree.ElementTree as ET


def get_req_progress(skey, rid):

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
        return -1
    else:
        progress = root[0][1][7].text
    print(progress)
    return int(progress)


if __name__ == '__main__':
    get_req_progress("c402c0b5-55c2-4697-ac40-fb55b88867ab", 3037)

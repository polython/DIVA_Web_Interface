import http.client
import xml.etree.ElementTree as ET


def get_session_code():

    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<xsd:registerClient xmlns:xsd=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xsd:appName>Tape Test Application</xsd:appName>\r\n    " \
              "<xsd:locName>1</xsd:locName>\r\n    " \
              "<xsd:processId>1</xsd:processId>\r\n" \
              "</xsd:registerClient>"

    headers = {
        'content-type': "application/xml",
        'accept': "application/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/registerClient", payload, headers)

    res = conn.getresponse()
    data = res.read()

# clientcode = xmltodict.parse(data.decode('UTF8'))

    root = ET.fromstring(data.decode('UTF8'))
    sessioncode = root[0].text

    print(sessioncode)
    return sessioncode

if __name__ == '__main__':
    get_session_code()




import http.client
import xml.etree.ElementTree as ET


def insert_tape(skey):

    sessionkey = str(skey)
    conn = http.client.HTTPConnection("172.24.183.26:9763")

    payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\">\r\n" \
              "<env:Body>\r\n" \
              "<p:insertTape xmlns:p=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">\r\n    " \
              "<xs:sessionCode xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">" + sessionkey +"</xs:sessionCode>\r\n    " \
              "<xs:require xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">0</xs:require>\r\n    " \
              "<xs:priorityLevel xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">50</xs:priorityLevel>\r\n    " \
              "<xs:acsId xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">0</xs:acsId>\r\n    " \
              "<xs:capId xmlns:xs=\"http://interaction.api.ws.diva.fpdigital.com/xsd\">0</xs:capId>\r\n    " \
              "</p:insertTape>\r\n" \
              "</env:Body>\r\n" \
              "</env:Envelope>"

    headers = {
        'accept': "application/xml",
        'content-type': "text/xml"
        }

    conn.request("POST", "/services/DIVArchiveWS_REST_2.1/insertTape", payload, headers)

    res = conn.getresponse()
    data = res.read()

    root = ET.fromstring(data.decode('UTF8'))
    sessioncode = root[0][1].text

    print(sessioncode)
    return sessioncode

if __name__ == '__main__':
    insert_tape("1afdd4d1-df1a-47f2-afe7-c2acba0349f2")

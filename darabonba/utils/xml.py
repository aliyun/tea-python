import xml.etree.ElementTree as ET
from darabonba.response import TeaResponse

class XML:

    @staticmethod
    def parse_xml(body, response: TeaResponse):
        try:
            tree = ET.ElementTree(ET.fromstring(body))
            root = tree.getroot()
            response.status_code = int(root.find('status_code').text)
            response.status_message = root.find('status_message').text
            response.headers = {header.tag: header.text for header in root.find('headers')}
            response.body = root.find('body').text
            return response
        except ET.ParseError as e:
            raise Exception('Error parsing XML: {}'.format(e))

    @staticmethod
    def to_xml(body):
        root = ET.Element("response")
        
        if 'status_code' in body:
            status_code = ET.SubElement(root, 'status_code')
            status_code.text = str(body['status_code'])
        
        if 'status_message' in body:
            status_message = ET.SubElement(root, 'status_message')
            status_message.text = body['status_message']
        
        if 'headers' in body:
            headers = ET.SubElement(root, 'headers')
            for key, value in body['headers'].items():
                header = ET.SubElement(headers, key)
                header.text = value
        
        if 'body' in body:
            body_elem = ET.SubElement(root, 'body')
            body_elem.text = body['body']
            
        xml_str = ET.tostring(root, encoding='unicode')
        return xml_str

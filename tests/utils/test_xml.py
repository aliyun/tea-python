import unittest
import xml.etree.ElementTree as ET
from darabonba.utils.xml import XML
from darabonba.response import TeaResponse

class TestXMLMethods(unittest.TestCase):

    def test_parse_xml_valid(self):
        body = """<response>
                    <status_code>200</status_code>
                    <status_message>OK</status_message>
                    <headers>
                        <Content-Type>application/xml</Content-Type>
                        <Content-Length>1234</Content-Length>
                    </headers>
                    <body>{"key": "value"}</body>
                  </response>"""
        expected_response = TeaResponse()
        expected_response.status_code=200
        expected_response.body='{"key": "value"}'
        expected_response.headers={'Content-Type': 'application/xml', 'Content-Length': '1234'}
        expected_response.status_message='OK'
        response = TeaResponse()
        result = XML.parse_xml(body, response)
        self.assertEqual(result.status_code, expected_response.status_code)
        self.assertEqual(result.status_message, expected_response.status_message)
        self.assertEqual(result.headers, expected_response.headers)
        self.assertEqual(result.body, expected_response.body)

    def test_parse_xml_invalid(self):
        body = """<response>
                    <status_code>200<status_code>
                    <status_message>OK</status_message>
                  </response>"""  # Missing a tag cloase potential mistake

        response = TeaResponse()
        with self.assertRaises(Exception) as context:
            XML.parse_xml(body, response)
        self.assertTrue('Error parsing XML' in str(context.exception))

    def test_to_xml(self):
        body = {
            'status_code': 200,
            'status_message': 'OK',
            'headers': {
                'Content-Type': 'application/xml',
                'Content-Length': '1234'
            },
            'body': '{"key": "value"}'
        }
        expected_xml_str = ("<response><status_code>200</status_code>"
                            "<status_message>OK</status_message><headers>"
                            "<Content-Type>application/xml</Content-Type>"
                            "<Content-Length>1234</Content-Length></headers>"
                            "<body>{\"key\": \"value\"}</body></response>")
        result = XML.to_xml(body)
        self.assertEqual(result, expected_xml_str)

import unittest
import os
from darabonba.utils.form import Form, FileField
from io import BytesIO

root_path = os.path.dirname(os.path.dirname(__file__))
file1 = os.path.join(root_path, 'utils/test_file.json')
file2 = os.path.join(root_path, 'utils/test.txt')

class TestForm(unittest.TestCase):
    
    def test_to_form_string(self):
        self.assertEqual("", Form.to_form_string(None))
        self.assertEqual("", Form.to_form_string({}))
        dic = {}
        dic["form"] = "test"
        dic["param"] = "test"
        self.assertEqual("form=test&param=test", Form.to_form_string(dic))
        dic = {
            'form': 'test',
            'param': 'test',
        }
        self.assertEqual("form=test&param=test", Form.to_form_string(dic))

    def test_get_boundary(self):
        boundary = Form.get_boundary()
        self.assertEqual(14, len(boundary))

    def test_to_file_from(self):
        # Test 1
        body = Form.to_file_form({}, 'boundary')
        for i in body:
            self.assertEqual('--boundary--\r\n'.encode(), i)

        form = {
            'stringkey1': 'string1',
            'stringkey2': 'string2'
        }
        body = Form.to_file_form(form, 'boundary')
        content = "--boundary\r\n" + \
                  "Content-Disposition: form-data; name=\"stringkey1\"\r\n\r\n" + \
                  "string1\r\n" + \
                  "--boundary\r\n" + \
                  "Content-Disposition: form-data; name=\"stringkey2\"\r\n\r\n" + \
                  "string2\r\n" + \
                  "--boundary--\r\n"
        form_str = b''
        for i in body:
            form_str += i
        self.assertEqual(content.encode(), form_str)
        # length: 86
        self.assertEqual(len(content.encode()), body.__len__())

        # # Test 2
        f1 = open(file1, encoding='utf-8')
        file_field1 = FileField(
            filename='test_file.json',
            content_type='application/json',
            content=f1
        )
        boundary = Form.get_boundary()
        form = {
            'stringkey': 'string',
            'filefield': file_field1
        }
        body = Form.to_file_form(form, boundary)

        content = "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"stringkey\"\r\n\r\n" + \
                  "string\r\n" + \
                  "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"filefield\"; filename=\"test_file.json\"\r\n" + \
                  "Content-Type: application/json\r\n" + \
                  "\r\n" + \
                  "{\"test\": \"tests1\"}" + \
                  "\r\n" + \
                  "--{}--\r\n".format(boundary)

        form_str = b''
        for i in body:
            form_str += i

        self.assertEqual(
            content.encode('utf-8'),
            form_str
        )
        # length: 247
        self.assertEqual(len(content.encode()), body.__len__())

        # Test 3
        f2 = open(file2, 'rb')
        file_field2 = FileField(
            filename='test.txt',
            content_type='application/json',
            content=f2
        )
        form = {
            'stringkey': 'string',
            'filefield1': file_field1,
            'filefield2': file_field2
        }
        body = Form.to_file_form(form, boundary)

        content = "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"stringkey\"\r\n\r\n" + \
                  "string\r\n" + \
                  "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"filefield1\"; filename=\"test_file.json\"\r\n" + \
                  "Content-Type: application/json\r\n" + \
                  "\r\n" + \
                  "{\"test\": \"tests1\"}" + \
                  "\r\n" + \
                  "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"filefield2\"; filename=\"test.txt\"\r\n" + \
                  "Content-Type: application/json\r\n" + \
                  "\r\n" + \
                  "test1test2test3test4" + \
                  "\r\n" + \
                  "--{}--\r\n".format(boundary)
        form_str = b''
        for i in body:
            form_str += i
        self.assertEqual(content.encode(), form_str)
        self.assertEqual(len(content.encode()), body.__len__())
        form_str = b''
        while True:
            r = body.read(1)
            if r:
                form_str += r
            else:
                break
        self.assertEqual(content.encode(), form_str)
        self.assertEqual(len(content.encode()), body.__len__())
        f2.close()

        # TEST 4
        f2 = open(file2, 'rb')
        io = BytesIO(f2.read())
        file_field2 = FileField(
            filename='test.txt',
            content_type='application/json',
            content=io
        )
        form = {
            'stringkey': 'string',
            'filefield1': file_field1,
            'filefield2': file_field2
        }
        body = Form.to_file_form(form, boundary)

        content = "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"stringkey\"\r\n\r\n" + \
                  "string\r\n" + \
                  "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"filefield1\"; filename=\"test_file.json\"\r\n" + \
                  "Content-Type: application/json\r\n" + \
                  "\r\n" + \
                  "{\"test\": \"tests1\"}" + \
                  "\r\n" + \
                  "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"filefield2\"; filename=\"test.txt\"\r\n" + \
                  "Content-Type: application/json\r\n" + \
                  "\r\n" + \
                  "test1test2test3test4" + \
                  "\r\n" + \
                  "--{}--\r\n".format(boundary)
        form_str = b''
        for i in body:
            form_str += i
        self.assertEqual(content.encode(), form_str)
        self.assertEqual(len(content.encode()), body.__len__())
        form_str = b''
        while True:
            r = body.read(1)
            if r:
                form_str += r
            else:
                break
        self.assertEqual(content.encode(), form_str)
        self.assertEqual(len(content.encode()), body.__len__())
        f1.close()
        f2.close()


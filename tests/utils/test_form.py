import unittest
from io import BytesIO
from darabonba.utils.form import Form, FileField
from darabonba.exceptions import RequiredArgumentException

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
            self.assertEqual(b'--boundary--\r\n', i)

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
        form_str = b''.join(body)
        self.assertEqual(content.encode(), form_str)
        self.assertEqual(len(content.encode()), len(form_str))

        # Test 2
        json_content = '{"test": "tests1"}'
        file_field1 = FileField(
            filename='test.json',
            content_type='application/json',
            content=BytesIO(json_content.encode('utf-8'))
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
                  "Content-Disposition: form-data; name=\"filefield\"; filename=\"test.json\"\r\n" + \
                  "Content-Type: application/json\r\n" + \
                  "\r\n" + \
                  json_content + \
                  "\r\n" + \
                  "--{}--\r\n".format(boundary)

        form_str = b''.join(body)

        self.assertEqual(content.encode('utf-8'), form_str)
        self.assertEqual(len(content.encode()), len(form_str))

        # Test 3
        text_content = b'test1test2test3test4'
        file_field2 = FileField(
            filename='test.txt',
            content_type='text/plain',
            content=BytesIO(text_content)
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
                  "Content-Disposition: form-data; name=\"filefield1\"; filename=\"test.json\"\r\n" + \
                  "Content-Type: application/json\r\n" + \
                  "\r\n" + \
                  json_content + \
                  "\r\n" + \
                  "--{}\r\n".format(boundary) + \
                  "Content-Disposition: form-data; name=\"filefield2\"; filename=\"test.txt\"\r\n" + \
                  "Content-Type: text/plain\r\n" + \
                  "\r\n" + \
                  text_content.decode('utf-8') + \
                  "\r\n" + \
                  "--{}--\r\n".format(boundary)
        
        form_str = b''.join(body)
        self.assertEqual(content.encode(), form_str)
        self.assertEqual(len(content.encode()), len(form_str))

    def test_to_form_string_skips_readable(self):
        form = {
            'a': '1',
            'f': BytesIO(b'x'),
        }
        self.assertEqual('a=1', Form.to_form_string(form))

    def test_file_form_chunked_len_and_refresh(self):
        content = b'0123456789abcdef'
        file_field = FileField(
            filename='chunk.txt',
            content_type='text/plain',
            content=BytesIO(content),
        )
        form = {
            'k': 'v',
            'file': file_field,
        }
        body = Form.to_file_form(form, 'boundary')
        total_len = len(body)
        self.assertGreater(total_len, 0)

        chunks = []
        while True:
            chunk = body.read(size=32)
            if not chunk:
                break
            chunks.append(chunk)
        joined = b''.join(chunks)
        self.assertEqual(total_len, len(joined))
        self.assertIn(b'chunk.txt', joined)

        body.refresh()
        refreshed = body.read()
        self.assertIn(b'chunk.txt', refreshed)

        class StrReadable:
            def __init__(self, data):
                self._data = data
                self._pos = 0
                self.len = len(data)

            def read(self, size=-1):
                if self._pos >= len(self._data):
                    return ''
                if size is None or size < 0:
                    size = len(self._data) - self._pos
                out = self._data[self._pos:self._pos + size]
                self._pos += len(out)
                return out

            def seek(self, *_args):
                self._pos = 0

        str_field = FileField(
            filename='s.txt',
            content_type='text/plain',
            content=StrReadable('hello-str'),
        )
        body2 = Form.to_file_form({'file': str_field}, 'b')
        data = b''.join(list(body2))
        self.assertIn(b'hello-str', data)


class TestFileField(unittest.TestCase):
    
    def test_file_field_validate(self):
        valid_file_field = FileField(filename="example.txt", content_type="text/plain", content="This is some text content.")
        
        # Test valid file field which should not raise any exception
        try:
            valid_file_field.validate()
        except Exception as e:
            self.fail(f"validate method raised an exception unexpectedly: {e}")

        # Test missing filename
        with self.assertRaises(RequiredArgumentException):
            invalid_file_field = FileField(content_type="text/plain", content="This is some text content.")
            invalid_file_field.validate()
        
        # Test missing content_type
        with self.assertRaises(RequiredArgumentException):
            invalid_file_field = FileField(filename="example.txt", content="This is some text content.")
            invalid_file_field.validate()
        
        # Test missing content
        with self.assertRaises(RequiredArgumentException):
            invalid_file_field = FileField(filename="example.txt", content_type="text/plain")
            invalid_file_field.validate()

    def test_to_map(self):
        file_field = FileField(filename="example.txt", content_type="text/plain", content="This is some text content.")
        expected_map = {
            "filename": "example.txt",
            "contentType": "text/plain",
            "content": "This is some text content."
        }
        
        self.assertEqual(file_field.to_map(), expected_map)

    def test_from_map(self):
        file_field = FileField()
        input_map = {
            "filename": "example.txt",
            "contentType": "text/plain",
            "content": "This is some text content."
        }
        
        file_field.from_map(input_map)
        
        self.assertEqual(file_field.filename, "example.txt")
        self.assertEqual(file_field.content_type, "text/plain")
        self.assertEqual(file_field.content, "This is some text content.")
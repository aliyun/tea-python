import uuid

class Form:

    @staticmethod
    def to_form_string(fields):
        """Converts a dictionary of fields to a form-encoded string."""
        if not isinstance(fields, dict):
            raise TypeError("The fields parameter must be a dictionary.")
        
        # Join the dictionary items in key=value pairs and separate them with &
        form_string = '&'.join(f'{key}={value}' for key, value in fields.items())
        return form_string

    @staticmethod
    def get_boundary():
        """Generates a unique boundary string for multipart form data."""
        # Generates a random UUID-based boundary
        return f'----WebKitFormBoundary{uuid.uuid4().hex}'

    @staticmethod
    def to_file_form(files, boundary=None):
        """Converts a dictionary of file data to a multipart form data string."""
        if not isinstance(files, dict):
            raise TypeError("The files parameter must be a dictionary.")
        
        if boundary is None:
            boundary = Form.get_boundary()
        
        lines = []
        for name, file_info in files.items():
            filename, content_type, content = file_info

            # Start with the boundary line
            lines.append(f'--{boundary}')
            # Add content disposition header
            lines.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"')
            # Add content type header
            lines.append(f'Content-Type: {content_type}')
            # Add a blank line to separate headers from content
            lines.append('')
            # Add the content
            lines.append(content)
        
        # Add the closing boundary
        lines.append(f'--{boundary}--')
        # Join all lines with newline characters
        return '\r\n'.join(lines)
import os

class File:
    
    @staticmethod
    def create_read_stream(file_path):
        """Creates a stream for reading a file."""
        try:
            return open(file_path, 'r')
        except FileNotFoundError:
            raise Exception(f'File not found: {file_path}')
        except Exception as e:
            raise Exception(f'Error opening file for read: {str(e)}')

    @staticmethod
    def create_write_stream(file_path):
        """Creates a stream for writing to a file."""
        try:
            return open(file_path, 'w')
        except Exception as e:
            raise Exception(f'Error opening file for write: {str(e)}')

    @staticmethod
    def exists(file_path):
        """Checks if a file exists."""
        return os.path.exists(file_path)

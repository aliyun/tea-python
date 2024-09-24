import json
import os.path
import aliyunsdkcore


def _load_json_from_data_dir(basename):
    base_dir = os.path.dirname(os.path.abspath(aliyunsdkcore.__file__))
    json_file = os.path.join(base_dir, "data", basename)
    with open(json_file) as fp:
        return json.loads(fp.read())

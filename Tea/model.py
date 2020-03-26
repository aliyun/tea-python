import re

from .exceptions import RequiredArgumentException


class TeaModel:
    _base_type = {int, float, bool, complex, str}
    _list_type = {list, tuple, set}
    _dict_type = {dict}

    def __init__(self):
        self._names = {}
        self._validations = {}

    @staticmethod
    def _entity_to_dict(obj):
        if type(obj) in TeaModel._dict_type:
            obj_rtn = {k: TeaModel._entity_to_dict(v) for k, v in obj.items()}
            return obj_rtn
        elif type(obj) in TeaModel._list_type:
            return [TeaModel._entity_to_dict(v) for v in obj]
        elif type(obj) in TeaModel._base_type:
            return obj
        elif isinstance(obj, TeaModel):
            prop_list = [(p, not callable(getattr(obj, p)) and p[0] != "_")
                         for p in dir(obj)]
            obj_rtn = {}
            for i in prop_list:
                if i[1]:
                    obj_rtn[obj._names.get(i[0]) or i[0]] = TeaModel._entity_to_dict(
                        getattr(obj, i[0]))
            return obj_rtn

    def to_map(self):
        prop_list = [(p, not callable(getattr(self, p)) and p[0] != "_")
                     for p in dir(self)]
        pros = {}
        for i in prop_list:
            if i[1]:
                pros[self._names.get(i[0]) or i[0]] = TeaModel._entity_to_dict(
                    getattr(self, i[0]))
        return pros

    def validate(self):
        self.validate_required()

    def validate_required(self):
        for attr_name in self._validations:
            if self._validations.get(attr_name).get("required"):
                v = getattr(self, attr_name)
                if v is None or v == "":
                    raise RequiredArgumentException(attr_name)

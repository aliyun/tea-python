from .exceptions import RequiredArgumentException


class TeaModel:
    _BASE_TYPE = (int, float, bool, complex, str)
    _LIST_TYPE = (list, tuple, set)
    _DICT_TYPE = (dict,)

    def __init__(self):
        self._names = {}
        self._validations = {}

    def _entity_to_dict(self, obj):
        if isinstance(obj, self._DICT_TYPE):
            obj_rtn = {k: self._entity_to_dict(v) for k, v in obj.items()}
            return obj_rtn
        elif isinstance(obj, self._LIST_TYPE):
            return [self._entity_to_dict(v) for v in obj]
        elif isinstance(obj, self._BASE_TYPE):
            return obj
        elif isinstance(obj, TeaModel):
            prop_list = [(p, not callable(getattr(obj, p)) and p[0] != "_")
                         for p in dir(obj)]
            obj_rtn = {}
            for i in prop_list:
                if i[1]:
                    obj_rtn[obj._names.get(i[0]) or i[0]] = self._entity_to_dict(
                        getattr(obj, i[0]))
            return obj_rtn

    def to_map(self):
        prop_list = [(p, not callable(getattr(self, p)) and p[0] != "_")
                     for p in dir(self)]
        pros = {}
        for i in prop_list:
            if i[1]:
                pros[self._names.get(i[0]) or i[0]] = self._entity_to_dict(
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


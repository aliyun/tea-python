from darabonba.model import DaraModel

class Event(DaraModel):
    def __init__(
        self,
        id: str = None,
        event: str = None,
        data: str = None,
        retry: int = None,
    ):
        self.id = id
        self.event = event
        self.data = data
        self.retry = retry

    def validate(self):
        self.validate_required(self.id, 'id')
        self.validate_required(self.event, 'event')
        self.validate_required(self.data, 'data')
        self.validate_required(self.retry, 'retry')

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.id is not None:
            result['id'] = self.id
        if self.event is not None:
            result['event'] = self.event
        if self.data is not None:
            result['data'] = self.data
        if self.retry is not None:
            result['retry'] = self.retry
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('id') is not None:
            self.id = m.get('id')
        if m.get('event') is not None:
            self.event = m.get('event')
        if m.get('data') is not None:
            self.data = m.get('data')
        if m.get('retry') is not None:
            self.retry = m.get('retry')
        return self
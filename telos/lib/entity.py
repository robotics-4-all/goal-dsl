from collections import deque

from telos.lib.types import Time


class Entity:
    def __init__(
        self,
        parent=None,
        name=None,
        etype=None,
        freq=None,
        topic=None,
        source=None,
        attributes=None,
        description="",
        **kwargs,
    ):
        self.parent = parent
        self.name = name
        self.camel_name = self._to_camel_case(name) if name else ""
        self.etype = etype
        self.freq = freq if freq not in (None, 0) else 1
        self.topic = topic
        self.state = {}
        self.source = source.ref if hasattr(source, "ref") else source
        self.attributes = attributes or []
        self.description = description
        self.attr_buffs = []
        self.attributes_dict = {attr.name: attr for attr in self.attributes}
        self.attributes_buff = {attr.name: None for attr in self.attributes}

        for attr_name, attribute in self.attributes_dict.items():
            if type(attribute) is DictAttribute:
                attribute.items_dict = {item.name: item for item in attribute.items}

    def get_buffer(self, attr_name):
        if len(self.attributes_buff[attr_name]) != self.attributes_buff[attr_name].maxlen:
            return [0] * self.attributes_buff[attr_name].maxlen
        else:
            return self.attributes_buff[attr_name]

    def init_attr_buffer(self, attr_name, size):
        self.attributes_buff[attr_name] = deque(maxlen=size)

    @staticmethod
    def _to_camel_case(snake_str):
        return "".join(x.capitalize() for x in snake_str.lower().split("_"))

    def update_state(self, new_state):
        self.state = new_state
        self.update_attributes(self.attributes_dict, new_state)
        self.update_buffers(self.attributes_buff, new_state)

    @staticmethod
    def update_buffers(root, state_dict):
        for attribute, value in state_dict.items():
            if root[attribute] is not None:
                root[attribute].append(value)

    @staticmethod
    def update_attributes(root, state_dict):
        for attribute, value in state_dict.items():
            if root[attribute].__class__.__name__ == "TimeAttribute":
                setattr(root[attribute].value, "hour", value["hour"])
                setattr(root[attribute].value, "minute", value["minute"])
                setattr(root[attribute].value, "second", value["second"])
            elif type(value) is dict:
                Entity.update_attributes(root[attribute].value, value)
            else:
                root[attribute].value = value


class Attribute:
    def __init__(self, parent=None, name=None, value=None, **kwargs):
        self.parent = parent
        self.name = name
        self.value = value


class IntAttribute(Attribute):
    def __init__(self, parent=None, name=None, default=None, generator=None, noise=None, **kwargs):
        super().__init__(parent, name, default)
        self.generator = generator
        self.noise = noise
        self.type = "int"
        if self.value is None:
            self.value = 0


class FloatAttribute(Attribute):
    def __init__(self, parent=None, name=None, default=None, generator=None, noise=None, **kwargs):
        super().__init__(parent, name, default)
        self.generator = generator
        self.noise = noise
        self.type = "float"
        if self.value is None:
            self.value = 0.0


class StringAttribute(Attribute):
    def __init__(self, parent=None, name=None, default=None, **kwargs):
        super().__init__(parent, name, default)
        self.type = "str"
        if self.value is None:
            self.value = ""


class BoolAttribute(Attribute):
    def __init__(self, parent=None, name=None, default=None, generator=None, **kwargs):
        super().__init__(parent, name, default)
        self.generator = generator
        self.type = "bool"
        if self.value is None:
            self.value = False


class TimeAttribute(Attribute):
    def __init__(self, parent=None, name=None, default=None, **kwargs):
        super().__init__(parent, name, default)
        self.type = "time"
        if self.value is None:
            self.value = Time(self, 0, 0, 0)


class ListAttribute(Attribute):
    def __init__(self, parent=None, name=None, default=None, generator=None, **kwargs):
        super().__init__(parent, name, default)
        self.generator = generator
        self.type = "list"
        if self.value is None:
            self.value = []


class DictAttribute(Attribute):
    def __init__(self, parent=None, name=None, items=None, generator=None, **kwargs):
        items = items or []
        value = {item.name: item for item in items}
        self.generator = generator
        self.type = "dict"
        super().__init__(parent, name, value=value)
        self.items = items

import json

class Episode(object):

    __instance_attributes = ('program', 'series', 'number_in_program', 'number_in_series', 'title',
                             'directors', 'writers', 'release', 'air', 'description')

    def __init__(self, **kwargs):
        self.__dict__.update({attr: value for attr, value in kwargs.items()
                              if attr in self.__class__.__instance_attributes})

    def __getattr__(self, attr):
        if attr not in self.__class__.__instance_attributes:
            raise AttributeError(attr)
        return self.__dict__.get(attr, None)

    def __setattr__(self, attr, value):
        if attr not in self.__class__.__instance_attributes:
            raise AttributeError(attr)
        self.__dict__[attr] = value

    def __repr__(self):
        return '{}(program="{}", title="{}")'.format(self.__class__.__name__, self.program, self.title)

    def as_json_obj(self):
        return {attr: value for attr, value in self.__dict__.items()
                if attr in self.__class__.__instance_attributes}

    def as_json(self):
        return json.dumps(self.as_json_obj())

    @classmethod
    def from_json(cls, json_string):
        return cls(**json.loads(json_string))

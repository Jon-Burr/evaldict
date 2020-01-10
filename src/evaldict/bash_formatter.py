import string

class BashFormatter(string.Formatter):

    @classmethod
    def parse(cls, format_string):

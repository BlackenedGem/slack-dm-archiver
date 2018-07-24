from enum import Enum
import argparse

class Switches:
    # region Switch definitions
    class dateModes(Enum):
        ISO8601 = '%Y-%m-%d'
        UK = '%d/%m/%Y'
    dateMode = dateModes.ISO8601
    # endregion

    # Set using arguments
    @classmethod
    def set_switches(cls, args: argparse.Namespace, parser: argparse.ArgumentParser):
        if 'date_format' in args:
            cls.dateMode = cls.convert_enum(cls.dateModes, args.date_format, "date format", parser)

    # Method to handle parsing switches properly
    @classmethod
    def convert_enum(cls, enum, string: str, switch_str: str, arg_parser: argparse.ArgumentParser):
        try:
            return enum[string.upper()]
        except KeyError:
            # noinspection PyProtectedMember
            arg_parser.error(
                "Could not interpret " + switch_str + ". Available options are: " + cls.list_enum(enum))

    @classmethod
    def list_enum(cls, enum):
        # noinspection PyProtectedMember
        return ', '.join(enum._member_names_)

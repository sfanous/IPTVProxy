from logging import Formatter


class MultiLineFormatter(Formatter):
    def format(self, record):
        formatted_string = Formatter.format(self, record)
        (header, footer) = formatted_string.split(record.message)
        formatted_string = formatted_string.replace('\n', '\n' + ' ' * len(header))

        return formatted_string

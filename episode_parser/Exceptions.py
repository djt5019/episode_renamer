class GeneralException(Exception):
    pass


class API_Exception(GeneralException):
    pass


class API_FileNotFoundException(API_Exception):
    pass


class API_FloodException(API_Exception):
    pass


class SettingsException(GeneralException):
    pass


class FormatterException(GeneralException):
    pass


class ShowException(GeneralException):
    pass

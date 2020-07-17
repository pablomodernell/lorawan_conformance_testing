class UiErrors(Exception):
    pass


class UiParsingError(UiErrors):
    pass


class SessionConfigurationBodyError(UiErrors):
    pass


class InputFieldError(UiErrors):
    pass


class UnsupportedFieldTypeError(InputFieldError):
    pass

class InputFormBody(UiErrors):
    pass
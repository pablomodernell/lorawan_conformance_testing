

class TestingToolError(Exception):
    """ Base exception for all kind of error in the testing tool."""
    pass


########################################################################
# Level 2
########################################################################
class UnknownTestError(TestingToolError):
    """ The test is not defined in the testing platform."""
    pass


class TestFailError(TestingToolError):
    """General exception thrown in case of a test failure."""
    def __init__(self, description, test_case, step_name, last_message=None):
        """
        :param description: description message of the failure.
        :param test_case: name of the test case.
        :param step_name: step of the tests.
        :param last_message: last message received.
        """
        self.last_message = last_message
        self.step_name = step_name
        self.test_case = test_case
        error_msg = description + "\n"
        error_msg += "Test: {0}\n".format(test_case)
        error_msg += "Step: {0}\n".format(step_name)
        if last_message:
            error_msg += "Last received message: \n{0}".format(last_message)
        super().__init__(error_msg)


class SessionTerminatedError(TestingToolError):
    """ Session terminated by the UI or SO."""
    pass


########################################################################
# Level 3
########################################################################
class SessionError(TestFailError):
    pass


class ConformanceError(TestFailError):
    """
    Test fail because of wrong format of a received message, with some header or field that differs from
    the LoRaWAN specification under test.
    """
    pass


class InteroperabilityError(TestFailError):
    pass


class TimeOutError(TestFailError):
    """
    Exception raised when the DUT doesn't send any response after a predefined lapse of time.
    """
    pass


########################################################################
# Level 4
########################################################################
class UnknownDeviceError(SessionError):
    """ The device was not registered in the testing platform."""
    pass


class JoinRejectedError(SessionError):
    """ The join request was rejected by the server."""
    pass


class UnexpectedResponseError(InteroperabilityError):
    """ Exception raised when the received message was not expected in the current step of the executed test."""
    pass


class WrongResponseError(InteroperabilityError):
    """ Exception raised when a correct test id is received but the content of the message is not correct."""
    pass

########################################################################
# Level 5
########################################################################


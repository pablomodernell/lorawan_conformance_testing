import conformance_testing.test_errors

########################################################################
# Level 2
########################################################################


########################################################################
# Level 3
########################################################################


########################################################################
# Level 4
########################################################################

class MessageFormatError(conformance_testing.test_errors.ConformanceError):
    """ Exception raised when the format of a LoRaWAN message has an error."""
    pass


class FrequencyError(conformance_testing.test_errors.InteroperabilityError):
    """ Exception raised when an error is detected with frequency used in a LoRaWAN message."""
    pass


class MACError(conformance_testing.test_errors.InteroperabilityError):
    """ Error while exchanging MAC commands."""
    pass

########################################################################
# Level 5
########################################################################


class MACPayloadError(MessageFormatError):
    """ Wrong MACPayload detected"""
    pass


class MHDRError(MessageFormatError):
    """ Wrong MAC Header (MHDR) detected"""
    pass


class MICError(MessageFormatError):
    """ Wrong MIC detected in the message."""
    pass


class EchoError(conformance_testing.test_errors.WrongResponseError):
    """ Exception raised when the ping pong echo message received was not equal as the expected."""
    pass


class ActokCounterError(conformance_testing.test_errors.WrongResponseError):
    """
    Exception raised when the downlink counter contained in an actok message doesn't match with the
    downlink count kept by the Testing App Server (TAS).
    """
    pass


class NoMACResponseError(MACError):
    """ No response was received to a MAC Request previouly sent."""
    pass


class WrongMACFormatError(MACError):
    """ The content of a MAC message doesn't follow the expected format."""
    pass


class MACConfigurationExchangeError(MACError):
    """ Error when trying to set configuration parameters using MAC commands."""
    pass

########################################################################
# Level 6
########################################################################


class FHDRError(MACPayloadError):
    """ Wrong Frame Header (FHDR) in the LoRaWAN data message."""
    pass


class FPortError(MACPayloadError):
    """ Wrong Frame Port (FPort) in the LoRaWAN data message."""
    pass


class FRMPayloadError(MACPayloadError):
    """ Wrong Frame Payload (FRMPayloadError) in the LoRaWAN data message."""
    pass


class JoinRequestError(MACPayloadError):
    """ Wrong Join Request message format."""
    pass


class MACPiggibackedAndPort0(MACPayloadError):
    """ MAC Commands are present in the FRMPayload (using Port 0) and also piggibacked in the FRMPayload, this
    message must be ignored."""
    pass

########################################################################
# Level 7
########################################################################


class DevAddrError(FHDRError):
    """ Wrong Device Addres (DevAddr) in the frame header."""
    pass


class FCtrlError(FHDRError):
    """ Wrong Frame Control (FCtrl) in the frame header."""
    pass


class FCntError(FHDRError):
    """ Wrong Frame Count (FCnt) in the frame header."""
    pass


class FOpts(FHDRError):
    """ Wrong Frame Options (FOpts) in the frame header."""
    pass


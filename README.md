# F-LoRA: LoRaWAN testing tool.
* [F-Interop](www.f-interop.eu)
* Region:  European Union 863-870MHz ISM Band 
* Protocol version: LoRaWAN Version 1.0.2/ Regional Parameters v1.0.2rB

## Quick start 

1. Create a user account [F-Interop](www.f-interop.eu) in [https://go.f-interop.eu/](https://go.f-interop.eu/).
2. Configure the LoRa gateway local.conf file to send the packets to an IP and UDP port in your LAN.
    * **local.conf** example:

    		                                                      
		           {"server_address": "192.168.0.129",
		           "serv_port_up": 5555,                          
		           "serv_port_down": 5555,                        
		           "serv_enabled": true,
		           "keepalive_interval": 10,        
		           "stat_interval": 30,             
		           "push_timeout_ms": 100,                        
		           "forward_crc_valid": true,                     
		           "forward_crc_error": false,                    
		           "forward_crc_disabled": false }
		           
3. Sign in and select the F-LoRa LoRaWAN conformance test.
4. Provide the device personalization information (ABP) using the web GUI:
    * DevEUI
    * AppKey
    * DevAddr
5. Select the test cases to be executed and follow instructions to install the Agent. The following environment 
variables must be defined:
    * AMQP_URL: URL of the AMQP broker with the connection parameters.
    * PF_IP: IP of the interface connected to the Gateway with the Packet Forwarder (the IP configured in the Gateway).
    * PF_UDP_PORT: UDP port used by the Packer Forwarder.
6. Start the Agent using the **flora_start_bridge** command.
6. Press the **Start** button in the web GUI.
7. Connect the Device Under Test (DUT) to start sending messages to the LoRa gateway.
    * The DUT with the Implementation Under Test (IUT) must implement the Test Application Protocol to enter in
    Test Mode (using the default testing port 224).


## Introduction
The f-LoRa testing tool is provided as an extension to the [F-Interop](www.f-interop.eu) platform in order to confirm
that a LoRaWAN MAC implementation running on an End Device fulfils the requirements of the LoRaWAN
protocol specification.

The Device Under Test (DUT) is a low power wireless end device implementing a LoRa PHY layer and the LoRaWAN MAC layer
Implementation Under Test (IUT). It runs a test application on top of that MAC layer. Duty cycle restrictions must be
disabled and the normal application should be suspended when the node enters the test mode.

The test bench consist of an Agent service running on the user side connected to a standard LoRa Gateway (provided by
the user) and a Test Application Server (TAS) that performs the tests. This tests will check that the devices behave
according to the specification, including the adaptive data rate mechanisms, encryption and message integrity code
calculation, frame format and timing of the reception windows.

### F-Interop integration
The user interacts with the F-LoRa testing tool using the [F-interop GUI](https://go.f-interop.eu/).
After the selection of the F-LoRa LoRaWAN testing tool, instructions are provided on how to download, run, and configure
the Agent module on the user's side.
The ABP credentials of the IUT (security keys, short address, device EUI) can be configured and then the user selects 
a group of tests to be performed.

An Agent serves as an interface between the gateway's packet forwarder and the testing tool.
The user must configure the gateway to send all the packets to the Agent component. 
Once the test session has started, all interactions are handled by the testing tool.
The testing application running on the device with the IUT responds as defined by the testing protocol.
A detailed description of the test verdict, indicating the errors found in any failing step is shown to the user in the 
GUI after all tests are completed. 

## Required components and pre-conditions
The user must provide a standard compliant LoRa gateway integrating a Packet Forwarder application. The LoRaWAN MAC
Implementation Under Test (IUT) will run on an end device that should be placed in a shielded container and conected
to the LoRa gateway by a radio connection.

## Test Application Protocol

Every test case is implemented as a series of steps that are coordinated by a test manager. For each step of the test
a message from the DUT is expected by the TAS and a response could be sent from the TAS to the DUT. This message
exchange follows a Test Application Protocol.

In order to be tested against the F-LoRa platform the DUT must implement a Test Mode in which the device is capable
of interacting with the Test Application Server following the Test Application Protocol. The normal traffic of the
regular applications of the node must be ignored until the test mode is deactivated.

When the DUT is configured in Test Mode it must send a periodic Test Activation OK (TAOK) message (period between 5
and 10 seconds). The TAOK message has a length of 2 bytes and consists of a downlink counter that is incremented by
the DUT every time it receive a test message from the TAS. 

To control the DUT behaviour, in order to test the IUT, the Test Application Protocol defines a set of messages. The
first byte of the FRMPayload of each application test message identifies its purpose:


| Test ID | First Byte (FRMPayload) | Name | Description |
|:-------:|:-----------------------:|:----:|:----------: |
| 0 | 0x00| Test deactivation | Deactivates the Test Mode in the DUT |
| 1 | 0x01| Test activation   | Activates the Test Mode (FRMPayload=0x01010101, port 224)|
| 0 | 0x02| Confirmed uplink  | Configures the test application in the DUT to use CONFIRMED uplink frames |
| 0 | 0x03| Unconfirmed uplink | Configures the test application in the DUT to use UNCONFIRMED uplink frames|
| 0 | 0x04| Ping Pong | Random payload. The DUT must respond with Test ID 4 and adding 1 to all bytes (modulo 256) |
| 0 | 0x06| Session update |Triggers a join request message exchange in order to update the device OTAA session. |

The Test Description document sould be used as a reference for more details on the Test Application Protocol.

### Test Description
A test description has been defined for testing the main specification of the LoRaWAN protocol.
The tests are classified into different groups, based on the type of features they aim to verify:

* ACT, device activation,
* FUN, basic functionalities and timing,
* SEC, security, encryption and integrity check,
* MAC, MAC commands.

The different activation mechanism, Activation By Personalization (ABP) and Over the Air Activation (OTAA) can be 
tested.
In addition to the basic joining message exchange of the OTAA, new data rate, reception windows delay, and frequencies
are configured using the Join Accept message to test the implementation of this feature.
Regarding security, end-to-end encryption with the configured keys can be tested and the Message Integrity Code 
calculation can be verified. Between the different messages exchanged with the IUT, new configuration parameters are
set using MAC commands to check that the IUT behaves as expected.

## Architecture overview
```

                                                                                            
                                                                                            
     F-Interop side                                                             +-------------+
                                          +-------------------------+           |             |
                                          |  Testing tool           |           |     RMQ     |
                                          |                         |           |    Broker   |
                                          |   +-----------------+   |           |             |
                                          |   |Test Application |   |           +------X------+
                                          |   |     Server      |   |    AMQP         XXX
                                          |   |      (TAS)      | <------------------> X <-+
                                          |   +-----------------+   |                      |
                                          +-------------------------+                      |
                                                                                           |
    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|XXXX
     User side                                                                             |
                                                                                           |
    +--------------------+                                                                 |
    |  End Device        |                                                             AMQP|
    |                    |                                                                 |
    | +----------------+ |                                                                 |
    | |Test application| |      +------------------------------+         +-----------+     |
    | +----------------+ |      |LoRa Gateway                  |         | Agent     |     |
    | |   LoRaWAN      | |      |                              | Semtech |           |     |
    | +----------------+ |      | +------------+ +-----------+ | Protocol| +-------+ |     |
    | |    LoRa        <---------->Concentrator| | Packet    | |         | |LoRaWAN| |     |
    | +----------------+ | LoRa | |            | | Forwarder <------------->Bridge <-------+
    |                    |      | +------------+ +-----------+ |  UDP    | +-------+ |
    +--------------------+      +------------------------------+         +-----------+

```
### Description of the components
* End Device: Device Under Test (DUT) implementing LoRaWAN Implementation Under Test (IUT) and running the test
 application that interacts with the test server.
* LoRa Gateway (provided by the user): LoRa concentrator and packet forwarder using semtech protocol.
* LoRaWAN Bridge: The Semtech Packet Forwarder Bridge is the service of the agent, provided by the testing platform, 
that runs on the user side. It encapsulates the packets coming from the gateway through a UDP connection into
AMQP packets. It publishes the messages with a routing key 'direcion.nwk.gatewayid' (e.g. up.nwk.gw1) and consumes the
downlink packets from the Test Application Server
* RMQ Broker: A Rabbit MQ message broker used to pass the messages between the Agent and the testing tool. 
* Test Application Server: is in charge of the test by exchanging tests requests (using port 224) and MAC commands
with the DUT while asserting that the communication follows the LoRaWAN specification. It coordinates the testing 
session, and has the information of the test to be run and the device session information with the session keys.


## Agent Service
The Agent is an application provided by the testing platform to be downloaded and installed on the user side. It 
consists of the following components:
* Agent Bridge: Captures the UDP packets comming from the Semtech Packet Forwarder installed in the LoRa gateway, and
sends them to the Test Application Server (TAS) using through the RabbitMQ message broker (using AMQP). It also consumes
the downlink messages comming from the TAS and forwards them to the LoRa gateway (to be sent to the end device).
* Packet Sniffer: Captures the hex dump of the LoRaWAN messages.
* Logger: Prints the log information of the Test platform.

### Agent Requirement
* Version 1.0.0
    * Python 3.5


## Testing tool messages
* Testing Tool Messages: messages exchanged between the different services of the testing tool (e.g. Agent and TAS).
* Gateway Messages: a Gateway Message is a Testing tool message composed of the LoRaWAN PHYPayload and the metadata
added by the gateway with information about the data rate, used frequency, timestap of the message, etc. They follow
the same structure and include the same metadata used by the Semtech Packet Forwarder protocol. The
**testingtool_messages** and **gateway_forwarder** modules implement the creation and parsing of this messages.

    ```
    {
    
        'tmst': 1604475836,
        'chan': 2,
        'rfch': 1,
        'freq': 868.5,
        'stat': 1,
        'modu': 'LORA',
        'datr': 'SF12BW125`',
        'codr': '4/5',
        'lsnr': 7.`8,
        'rssi': -23,
        'size': 29,
        'data': 'QJ8pKAGAAAACBq6JhF/uO9ZeeoSq4xZMFchm3lw='
    }
    ```

### Message Queuing
The **message_broker** module in the parameters package provides the routing keys used by the testing tool components
to exchange data and configuration messages. All the services use this module for flexibility in the definition of the
routing keys.
* Routing Keys
    * Uplink message examples: 
        * fromAgent.gw1: uplink network message published by LoRaWAN Bridge (gw1 identifies the gateway)
    * Downlink message examples:
        * toAgent.gw1: downlink network message published by the Test Server.


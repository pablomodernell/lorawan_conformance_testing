from setuptools import setup, find_packages

MAJOR = 1
MINOR = 1
PATCH = 4
VERSION = "{}.{}.{}".format(MAJOR, MINOR, PATCH)

name = 'lorawan_conformance'
description = "LoRaWAN conformance testing user Agent tools."


CLASSIFIERS = [
    "Development Status :: 1 - Betha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Internet",
    "Topic :: Software Development :: Testing",
    "Topic :: Scientific/Engineering",
    "Operating System :: POSIX",
    "Operating System :: Unix",
    "Operating System :: MacOS"
]

with open("version.py", "w") as f:
    f.write("__version__ = '{}'\n".format(VERSION))

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(name=name,
      author="Pablo Modernell",
      author_email="pablomodernell@gmail.com",
      mantainer="Pablo Modernell",
      mantainer_email="pablomodernell@gmail.com",
      description=description,
      version=VERSION,
      packages=find_packages(),
      py_modules=['utils', 'message_queueing', 'logger_configurator'],
      include_package_data=True,
      install_requires=[
          'click==6.7',
          'pika==0.12.0',
          'pycryptodomex==3.6.6'
      ],
      entry_points={
          'console_scripts': [
              'cl_start_bridge = lorawan.user_agent.bridge.bridge_main:agent_main',
              'cl_msg_forging = lorawan.user_agent.messenger.agent_mock:agent_mock_main',
              'cl_sniffer = lorawan.user_agent.packet_sniffer.sniffer_main:sniff',
              'cl_log_tas = lorawan.user_agent.logger.log_main:log_test_session_coordinator',
              'cl_log_all = lorawan.user_agent.logger.log_main:log_all',
              'cl_send = lorawan.user_agent.messenger.cli_main:send',
              'cl_configure_device_mock = lorawan.user_agent.messenger.cli_main:configure_device_mock',
              'cl_send_actok = lorawan.user_agent.messenger.cli_main:send_actok',
              'cl_send_join = lorawan.user_agent.messenger.cli_main:send_join',
              'cl_send_pong = lorawan.user_agent.messenger.cli_main:send_pong',
              'cl_show_info = lorawan.user_agent.messenger.cli_main:show_info',
              'cl_tas_config = lorawan.user_agent.messenger.cli_main:send_tas_config',
              'cl_tas_start = lorawan.user_agent.messenger.cli_main:send_start_signal',
              'cl_tas_device = lorawan.user_agent.messenger.cli_main:send_deviceid_to_tas',
          ]
      },
      )

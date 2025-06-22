# Silence

Silence is an open-source, cross-platform adversary emulation and red team framework designed to help organizations of all sizes conduct comprehensive security testing. Its primary purpose is to stage and manage reverse shells, making it an essential tool for penetration testers and security professionals.

The server is supported on Windows and Linux.

[![Python](https://img.shields.io/badge/Python-%E2%89%A5%203.6-yellow.svg)](https://www.python.org/)
<img src="https://img.shields.io/badge/Developed%20on-Windows%2011-1677CF">
[![License](https://img.shields.io/badge/License-BSD%203%20Clause%20license-C91515)](https://github.com/SilentisVox/Silence/blob/master/LICENSE)
<img src="https://img.shields.io/badge/Maintained%3F-Yes-1FC408">

### Features

- Interactive CLI
- Argument Parsing for Configuration
- TCP Reverse-Shell Handler
- HTTP Stager
- Payload Generation
- Session Management Commands
- Service Control Commands
- Utility Commands
- Core Client-Side Payload
- Colorized Output and Formatting

### Setup

```
git clone https://github.com/SilentisVox/Silence
cd Silence
python3 Silence.py
```

### Usage

```
python3 Silence.py [-h] -c [callback_address] -l [handler_port] -p [stager_port]
```

### Demo

<p align="center">
  <sup>Video Demo on YouTube</sup>
  <br>
  <a href="https://youtu.be/JKp0YGE0NFw">
    <img src="assets/Silence.jpg" alt="Demo" />
  </a>
</p>

```
 → python Silence.py -h

    ┌─┐┬ ┬  ┌─┐┌┐┌┌─┐┌─┐
    └─┐│ │  ├- ││││  ├-
    └─┘┴ ┴─┘└─┘┘└┘└─┘└─┘
                Descends

usage: Silence.py [-h] [-c C] [-p P] [-l L]

options:
  -h, --help  show this help message and exit
  -c C        Callback address
  -p P        TCP Handler port (Default 4443)
  -l L        HTTP Stager port (Default 8080)
```
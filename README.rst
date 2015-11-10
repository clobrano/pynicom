Pynicom: A Minicom like shell in Python
=======================================

Pynicom reproduces the behavior of Minicom, adding some utilities:

* command history
* autocompletion
* inline help
* pattern highlight (optional)

Auto-completion and inline help are available using a _dictionary_
file. Each entry in the file has the format

    command-name        # <inline-help>

    e.g.

         AT+FCLASS           # Select Active Service Class
         AT+GCAP             # Capabilities list
         AT+GMI              # Manufacturer identification

Of course all the commands written in the command-line are sent to the
serial device even if they are not in the dictionary file.

_dictionary_ file is saved as hidden file in your HOME folder and named _.pynicom-dictionary_and it is **empty** when Pynicom is first installed. Feel free to copy the example on Pycom's project page on [GitHub](https://github.com/clobrano/pynicom.git) in your own dictionary file.


Installation
------------

1. Install PyPI module manager

    sudo apt-get install python-pip

2. Install dependencies: docopt, pyserial, readline (optional [raffaello](https://pypi.python.org/pypi/raffaello/) for pattern highlight)

    sudo pip <module-name>


Usage
-----

On GNU/Linux, Pynicom need administrative privilegies to access the serial device. On Debian/Ubuntu and derivates this can be done running the following command:

    $ sudo pynicom


First steps
-----------

Auto-completion is obtained with with a double tab

    A Minicom like shell in Python3
    author: Carlo Lobrano
    version: 0.1.0

    Usage:
        pynicom [-d|--debug] [--port=port --baud=rate --bytesize=bytesize --parity=parity --stopbits=stopbits --sw-flow-ctrl=xonxoff --hw-rts-cts=rtscts --hw-dsr-dtr=dsrdtr --timeout=timeout]


    (no-conn)<Tab><Tab>
    AT               at               exit             quit             serial_info      serial_read      set_bytesize     set_parity       set_stopbits     shell
    ATE              ate              help             serial_close     serial_open      set_baudrate     set_debug        set_port         set_timeout      show_dictionary
    (no-conn)


a known limitation is that the extended commands (+,&,#,...) are auto-completed after typing at least the symbol

    (/dev/ttyACM0 @ 115200) at<Tab><Tab>
    at   ate
    (/dev/ttyACM0 @ 115200) at+<Tab><Tab>
    CGDCONT  CGI      CGREG    CREG     FCLASS   GCAP     GMI      GMM      GMR      GSN
    (/dev/ttyACM0 @ 115200) at+


As you could see, the prompt shows the current serial device used and the baud rate or "no-conn".

To use the **inline help**, issue the command: 'help command-name' or '?command-name'

    (no-conn) help serial_open

       Open the given serial device.

       Example:
       serial_open /dev/ttyUSB0 115200 8 N 1  False False False 1

       where the args are respectively: port, baudrate, bytesize, parity, stopbits, SW flow control, HW flow control RTS/CTS, HW flow control DSR/DTR, timeout. You do not need to give all the parameters, if you are fine with the default values, just give the serial device path.


The connection to the serial device can be established also with Pynicom arguments:

    $ sudo pynicom --port=/dev/ttyACM0 --baud=115200

    A Minicom like shell in Python
    author: Carlo Lobrano
    version: 0.1.0

    Usage:
        pynicom [-d|--debug] [--port=port --baud=rate --bytesize=bytesize --parity=parity --stopbits=stopbits --sw-flow-ctrl=xonxoff --hw-rts-cts=rtscts --hw-dsr-dtr=dsrdtr --timeout=timeout]


    (/dev/ttyACM0 @ 115200)

To see all input arguments type

    $ pynicom -h

Connection parameters can be changed using the `set_` commands without closing and opening again the connection:

    (/dev/ttyACM0 @ 115200) set_
    set_baudrate  set_bytesize  set_debug     set_parity    set_port      set_stopbits  set_timeout


`serial_info` shows the current connection's info

    (/dev/ttyACM0 @ 115200) serial_info
            Serial<id=0x7fbf8df8af50, open=True>(port='/dev/ttyACM0', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)


the special character '!' execute system's commands:

    (/dev/ttyACM0 @ 115200) !ls -la
    total 25
    drwxrwx--- 1 root vboxsf     0 lug  2 10:25 .
    drwxrwx--- 1 root vboxsf  4096 lug  2 10:25 ..
    -rwxrwx--- 1 root vboxsf  1439 lug  2 08:57 dictionary.txt
    -rwxrwx--- 1 root vboxsf     1 lug  2 08:57 errors.txt
    -rwxrwx--- 1 root vboxsf     0 lug  2 08:57 __init__.py
    -rwxrwx--- 1 root vboxsf 15417 lug  2 10:24 pynicom.py
    -rwxrwx--- 1 root vboxsf   390 lug  2 08:57 test.py
    -rwxrwx--- 1 root vboxsf  2115 lug  2 08:57 tests.py


All commands have 1 seconds timeout as default, but that can be changed with `set_timeout` command. If a command does not return, stop it with CTRL-B or CTRL-C


Highlight patterns
------------------

The [Raffaello](https://pypi.python.org/pypi/raffaello/) module allows Pynicom to highlight the text ouput. You can choose a pattern to be highlighted in a given color (the available colors depending on the Shell)

    (/dev/ttyUSB0 @ 9600) highlight GNRMC=>green

this can be useful when reading NMEA sentences for example (with `serial_read`)

use `show_highlight` to see the current highlighted patterns and `remove_highlight` to remove a pattern.

    (/dev/ttyUSB0 @ 9600) show_highlight
            {'GNRMC': green}
    (/dev/ttyUSB0 @ 9600) remove_highlight GNRMC
    (/dev/ttyUSB0 @ 9600) show_highlight
            {}


NMEA sentences
--------------

Nmea sentences can be sent to the serial device using the `nmea` command. Pycom will automatically add the initial '$' symbol, the checksum and the final appendix (<CR><LF>), so that a possible usage of this API is the following:

(/dev/ttyUSB0 @ 9600) nmea PMTK430
        nmea > "$PMTK430*35<CR><LF>"
            $GLGSV,2,1,06,84,81,030,43,74,78,042,46,85,44,215,48,73,35,128,36*62
            $GLGSV,2,2,06,75,31,326,44,83,25,033,44*68
            $GNRMC,115725.000,A,3913.6604,N,00904.1282,E,0.00,51.50,060715,,,D*4C
            $GNVTG,51.50,T,,M,0.00,N,0.01,K,D*16
            $PMTK530,0*28


after sending the nmea message, pynicom will automaticalli issue `serial_read` command. You will stop reading using CTRL-C.

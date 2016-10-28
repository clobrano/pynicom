#!/usr/bin/env python
"""
A Minicom like shell in Python
author: Carlo Lobrano

Usage:
    pynicom [-d|--debug] [--port=port --baud=rate --bytesize=bytesize --parity=parity --stopbits=stopbits --sw-flow-ctrl=xonxoff --hw-rts-cts=rtscts --hw-dsr-dtr=dsrdtr --timeout=timeout] [--atcmd=atcmd]

"""

from cmd import Cmd
from docopt import docopt
import serial
from time import sleep
import glob
import logging
import os
import readline as rl
import sys
import errno

try:
    import raffaello
    color = True
    patterns = {}
except ImportError:
    color = False

rl.set_completer_delims(' \t\n"\\\'`@$><=;|&{(?+#/%')

logger = logging.getLogger('pynicom')
logi = lambda x: logger.info(x)
loge = lambda x: logger.error(x)
logw = lambda x: logger.warn(x)
logd = lambda x: logger.debug(x)

PYTHON3 = sys.version_info > (2.7, 0)
HOME = os.path.expanduser('~')
HISTORY = os.path.join(HOME, '.pynicom-history')
DICTIONARY = os.path.join(HOME, '.pynicom-dictionary')

class Pynicom(Cmd):
    STD_BAUD_RATES = ['300', '1200', '2400', '4800', '9600', '19200', '28800', '38400', '57600', '115200', '153600', '2304000', '460800', '500000', '576000', '921600']
    PROMPT_FMT = '(%s@%d) '
    PROMPT_DEF = '(no-conn) '

    _cmd_dict = {}
    connection = None
    last_serial_read = None
    last_serial_write = None
    toread = False
    _port_config = {
            'port':'/dev/ttyUSB0', 'baudrate':115200, 'bytesize':8,
            'parity':'N', 'stopbits':1, 'xonxoff':False,
            'rtscts':False, 'dsrdtr':False, 'timeout':1
            }

    def do_dictionary(self, string = None):
        """
        If no keyword is provided, it shows all the known commands. If a keyword
        is provided, it shows only matching known commands.
        """
        if self.__is_string_empty(string):
            logd('Emtpy search string')
            for name in self._cmd_dict:
                print('  %s: %s' % (name, self._cmd_dict [name]))
        else:
            logd('Looking for "%s" in dictionary' % string)

            matches = [ name for name in self._cmd_dict if (string.lower() in name.lower()) or (string.lower() in self._cmd_dict[name].lower())]

            if 0 == len(matches):
                print('No match found')
            else:
                for match in matches:
                    print('  %s: %s' % (match, self._cmd_dict [match]))

    def do_AT(self, string):
        """Send AT commands to a connected device"""
        self.do_at(string)

    def complete_AT(self, text, line, begidx, endidx):
        return self.complete_at(text, line, begidx, endidx)

    def do_at(self, string):
        """Send AT command to a connected device."""
        if self.__is_valid_connection():
            self.serial_write('at%s' % string)

    def complete_at(self, text, line, begidx, endidx):
        #logd('complete_at: %s, %s, %d, %d' % (text, line, begidx, endidx))
        completions = [key [begidx:] for key in self._cmd_dict.keys() if key.lower().startswith(line.lower())]
        return completions

    def do_serial_info(self, string=''):
        """Print out info about the current serial connection"""
        if self.__is_valid_connection():
            print(self.connection)

    def do_serial_open(self, string):
        """
        Open the given serial device.

        Example:
        serial_open /dev/ttyUSB0 115200 8 N 1 False False False 1

        where the args are respectively: port, baudrate, bytesize, parity, stopbits, SW flow control, HW flow control RTS/CTS, HW flow control DSR/DTR, timeout
        """

        for id, arg in enumerate(string.split(' ')):
            if 0 == id:
                self._port_config ['port'] = arg
            if 1 == id:
                self._port_config ['baudrate'] = arg
            if 2 == id:
                self._port_config ['bytesize'] = int(arg)
            if 3 == id:
                self._port_config ['parity'] = arg
            if 4 == id:
                self._port_config ['stopbits'] = int(arg)
            if 5 == id:
                self._port_config ['xonxoff'] = eval(arg)
            if 6 == id:
                self._port_config ['rtscts'] = eval(arg)
            if 7 == id:
                self._port_config ['dsrdtr'] = eval(arg)
            if 8 == id:
                self._port_config ['timeout'] = int(arg)

        logd('Connecting with the following params {0}.'.format(self._port_config))

        try:
            self.connection = serial.Serial(
                    port        = self._port_config ['port'],
                    baudrate    = self._port_config ['baudrate'],
                    bytesize    = self._port_config ['bytesize'],
                    parity      = self._port_config ['parity'],
                    stopbits    = self._port_config ['stopbits'],
                    xonxoff     = self._port_config ['xonxoff'],
                    rtscts      = self._port_config ['rtscts'],
                    dsrdtr      = self._port_config ['dsrdtr'],
                    timeout     = self._port_config ['timeout']
                    )

        except (ValueError, serial.SerialException) as err:
            loge(err)

        if self.__is_valid_connection():
            self.prompt = self.__set_prompt()

    def complete_serial_open(self, text, line, begidx, endidx):
        """
        Autocomplete for serial_open command
        """
        nargs = len(line.split(' '))

        if 2 == nargs:
            completions = self.complete_set_port(text, line, begidx, endidx)

        elif 3 == nargs:
            completions = self.complete_set_baudrate(text, line, begidx, endidx)

        elif 5 == nargs:
            completions = self.complete_set_parity(text, line, begidx, endidx)

        else:
            completions = []

        return completions

    def do_set_port(self, string):
        """
        Set serial device fullpath for the connection
        """
        if self.__is_valid_connection():
            try:
                self.connection.port = string
                self.prompt = self.__set_prompt()
            except (serial.serialutil.SerialException) as err:
                logd(err)

    def complete_set_port(self, text, line, begidx, endidx):
        """
        Autocomplete for set_port command
        """
        before_arg = line.rfind(" ", 0, begidx)

        if -1 == before_arg:
            return # arg not found

        fixed   = line [before_arg + 1 : begidx]  # fixed portion of the arg
        arg     = line [before_arg + 1 : endidx]
        pattern = arg + '*'

        return [path.replace(fixed, "", 1) for path in glob.glob(pattern)]

    def do_set_baudrate(self, string):
        """Set connection baud rate"""
        if self.__is_valid_connection():
            self.connection.baudrate = string
            self.prompt = self.__set_prompt()

    def complete_set_baudrate(self, text, line, begidx, endidx):
        """
        Autocomplete for set_baudrate command
        """
        token = line [begidx : endidx + 1]
        return [rate for rate in self.STD_BAUD_RATES if rate.startswith(token)]

    def do_set_bytesize(self, string):
        """Set serial connection bytesize"""
        if self.__is_valid_connection():
            self.connection.bytesize = int(string)

    def do_set_parity(self, string):
        """Set serial connection parity"""
        if self.__is_valid_connection():
            self.connection.parity = string

    def complete_set_parity(self, text, line, begidx, endidx):
        """
        Autocomplete for set_parity command
        """
        return ['N' 'O']

    def do_set_stopbits(self, string):
        """Set serial connection stopbits"""
        if self.__is_valid_connection():
            self.connection.stopbits = int(string)

    def do_set_timeout(self, string):
        """Set serial connection timeout"""
        if self.__is_valid_connection():
            self.connection.timeout = int(string)

    def do_serial_read(self, mode = ''):
        """Read from serial device. Press CTRL-C to interrupt it.

        Keyword arguments:
        mode -- if its value is 'nostop', keep reading even if read 0 bytes.
        """

        allowed_zero_read = 3

        while allowed_zero_read > 0 or 'nostop' in mode:
            try:
                if not PYTHON3:
                    logd('reading without decode')
                    read = self.connection.readline().rstrip()
                else:
                    logd('reading with decode')
                    read = self.connection.readline().decode().rstrip()

                logd('got "%s"' % read)

                if self.__is_echo(read):
                    logd('Got echo (%s)' % read)
                    continue

                if len(read):
                    if None != self.last_serial_write and self.last_serial_write.lower() != 'at' and 'OK' == read:
                        continue
                    else:
                        self.last_serial_read = read
                        print('%s%s' % (' '*len(self.prompt), read))
                elif 0 < allowed_zero_read:
                    logd('stop read counter %d' % allowed_zero_read)
                    allowed_zero_read -= 1
                    continue
                else:
                    logd("Nothing to read, exiting")
                    break

            except (OSError,serial.serialutil.SerialException) as error:
                loge("Got SerialException/OSerror (%d)" % allowed_zero_read);
                loge(error)
                allowed_zero_read -= 1
            except KeyboardInterrupt:
                logw('Keyboard interrupt')
                break

    def complete_serial_read(self, text, line, begidx, endidx):
        """
        Autocomplete for serial_read
        """
        return ['nostop']

    def do_clear_history(self, string):
        """Clear command history"""
        logw('Clearing history')
        rl.clear_history()

    def do_set_history_length(self, string):
        """Set the maximum number of commands that will be stored in history file"""
        set_history_length(eval(string))

#    def do_get_history_length(self, string):
#        """Return the current maximum number of commands stored in history file"""
#        print get_history_length()

    def do_history(self, string):
        history_len = rl.get_current_history_length()
        for i in range(history_len):
            print(rl.get_history_item(i))

    def preloop(self):
        Cmd.preloop(self)
        if os.path.exists(HISTORY):
            logd('Reading history')
            rl.read_history_file(HISTORY)

    def postloop(self):
        self.save_history()
        Cmd.postloop(self)

    def save_history(self):
        logd('Saving history...')
        rl.write_history_file(HISTORY)

    def postcmd(self, stop, line):
        if self.toread:
            self.do_serial_read('')
            self.toread = False
        return stop

    def do_serial_close(self, string=''):
        """Close serial connection (if any)"""

        if self.__is_valid_connection():
            self.connection.close()
            self.prompt = self.PROMPT_DEF
            self._port_config = {
                    'port':'/dev/ttyUSB0', 'baudrate':115200, 'bytesize':8,
                    'parity':'N', 'stopbits':1, 'xonxoff':False,
                    'rtscts':False, 'dsrdtr':False, 'timeout':1
                    }
            logi('connection closed')

    def do_exit(self, string=''):
        """Exit from pynicom shell"""
        self.do_serial_close()
        self.save_history()
        sys.exit(0)

    def do_quit(self, string=''):
        """Exit from pynicom shell"""
        self.do_serial_close()
        sys.exit(0)

    def do_shell(self, cmd):
        os.system(cmd)

    def do_help(self, string = ''):
        if '' != string:
            logd('help for %s' % string)

        if (string.upper() in self._cmd_dict.keys()):
            print('\t%s' % self._cmd_dict [string.upper()])

        elif (string.lower() in self._cmd_dict.keys()):
            print('\t%s' % self._cmd_dict [string.lower()])

        else:
            Cmd.do_help(self, string)

    def do_set_debug(self, string='True'):
        """Enable/Disable debug"""
        if 'true' == string.lower():
            set_debug(True)
        elif 'false' == string.lower():
            set_debug(False)
        else:
            loge("Wrong argument %s (expected 'True or False')" % string)

    def complete_set_debug(self, text, line, begidx, endidx):
        completions = ['False', 'True']

    def do_nmea(self, string):
        sentence = self.__nmea_format(string)
        print('nmea > "$%s<CR><LF>"' % sentence)
        self.serial_write('$' + sentence, appendix = '\r\n')

    def complete_nmea(self, text, line, begidx, endidx):
        custom_msg = ['PMTK', 'PSRF']
        if 0 >= len(text):
            return custom_msg
        else:
            return [cmd for cmd in custom_msg if cmd.startswith(text.upper())]

    def default(self, line):
        self.__send_raw(line)

    def emptyline(self):
        """
        Default emptyline will repeat last command, while usually that is not
        the expected behavior in a Shell
        """
        pass

    def serial_write(self, msg, appendix='\r'):
        try:
            msg_cr = msg + appendix
            logd('sending: "%s"' % repr(msg_cr))
            if not PYTHON3:
                logd('No encode')
                bytes = self.connection.write(msg_cr)
                logd("wrote %d bytes" % bytes)
            else:
                logd('encode')
                bytes = self.connection.write(msg_cr.encode())

            if 0 >= bytes:
                logd('Wrote %d bytes' % bytes)
            else:
                self.last_serial_write = msg
                self.toread = True

        except (TypeError) as err:
            loge('Could not write msg "%s": %s' % (msg, err))

    def __is_valid_connection(self):
        logd('check connection')
        retval = True
        if (None == self.connection) or (not self.connection.isOpen()):
            logd('No serial connection established yet')
            retval = False
        return retval

    def __send_raw(self, string=''):
        """Let the user send raw messages to the serial device"""
        if self.__is_valid_connection():
            self.serial_write(string)

    def __is_string_empty(self, string):
        return (None == string or 0 == len(string))

    def __is_echo(self, string):
        retval = (string == self.last_serial_write)
        return retval

    def __set_prompt(self):
        logd(self.connection.baudrate)
        return self.PROMPT_FMT % (self.connection.port, self.connection.baudrate)

    def __nmea_format(self, message):
        checksum = self.__nmea_checksum(message)
        well_formed_message = '%s*%s' % (message, checksum)
        return well_formed_message

    def __nmea_checksum(self, message):
        checksum = 0

        for c in message:
            checksum ^= ord(c)

        return '%02X' % checksum

    def do_highlight(self, string):
        if color:
            global patterns
            try:
                new_entry = raffaello.parse_color_option(string)
                patterns.update(new_entry)
            except Exception as err:
                loge('Could not highlight "%s". Error %s' % (string, err))

        else:
            loge('Highlightning not available. Raffaello module not found')

    def do_show_highlight(self, string):
        if color:
            global patterns
            print(patterns)
        else:
            loge('Highlightning not available. Raffaello module not found')

    def do_remove_highlight(self, string):
        if color:
            global patterns
            if string in patterns.keys():
                del patterns [string]
            else:
                logi('Pattern "%s" is not highlighted' % string)
        else:
            loge('Highlightning not available. Raffaello module not found')



def get_commands(string_list):
    if 0 == len(string_list):
        loge('No data to generate known command list')
        return

    commands = {}
    at_cmd = None
    at_cmd_doc = ''
    for string in string_list:
        if 0 == len(string):
            continue

        logd('-- Parsing %s' % string.rstrip())
        if string.lower().startswith('at'):

            if None != at_cmd and 0 != len(at_cmd_doc):
                logd('Adding doc %s to %s' % (at_cmd_doc, at_cmd))
                commands [at_cmd] = at_cmd_doc
                at_cmd_doc = ''

            else:
                logd('No doc to update (at_cmd: {0}, at_cmd_doc {1})'.format(at_cmd, at_cmd_doc))

            short_help = 'no help found'
            if (' # ' in string) or (' #' in string):
                logd('Inline short help found')
                string, short_help = string.split(' # ')
                logd(string)

            at_cmd = string.strip()
            at_key = string [2]
            cmd = string [3:].strip()

            logd('adding %s to dict for at%s' % (at_cmd, at_key))
            commands [at_cmd] = short_help.rstrip()

        if string.startswith('#'):
            logd('Got doc for at cmd %s' % at_cmd)
            at_cmd_doc += string [1:]   # skip initial '#'

    return commands

def stub_do_func(instance, string):
    if (None == instance.connection) or (not instance.connection.isOpen()):
        logi('No serial connection established yet')
    else:
        cmd = '%s' % string
        instance.serial_write(cmd)

def contains_symbols(string, symbols):
    set_sym = set(symbols)
    set_str = set(string)

    retval = (0 != len(set_sym.intersection(set_str)))
    logd('{0} contains {1}? {2}'.format(string, set_sym, retval))

    return retval

def add_do_command(commands, cls):
    for cmd in commands.keys():
        if not contains_symbols(cmd, '+%&$\#/'):
            logd("Adding %s" % cmd)
            setattr(cls, 'do_%s' % cmd, stub_do_func)

            if cmd.isupper():
                setattr(cls, 'do_%s' % cmd.lower(), stub_do_func)
            else:
                setattr(cls, 'do_%s' % cmd.upper(), stub_do_func)

def run(shell):
    """Run pynicom shell"""
    try:
        shell.cmdloop(__doc__)
    except KeyboardInterrupt:
        shell.save_history()
        logi("Keyboard interrupt")
    except IOError, err:
        loge(err)
        logi("Try running with superuser privilegies")

    if None != shell.connection and shell.connection.isOpen():
        shell.do_serial_close('')

def init(arguments = {}):
    """Initialize list of known commands and pynicom shell"""
    shell = Pynicom()

    try:
        if os.path.exists(DICTIONARY):
            logi('Loading dictionary %s' % DICTIONARY)
            known_commands = get_commands(open(DICTIONARY, 'r').readlines())

            if len(known_commands) == 0:
                logw('No commands in dictionary file %s' % DICTIONARY)
            else:
                add_do_command(known_commands, Pynicom)
                shell._cmd_dict = known_commands
                logi('Dictionary loaded')
    except IOError, err:
        if errno.ENOENT != err.errno:
            loge('IOERROR accessing %s: %s' % (DICTIONARY, err))
            sys.exit(1)

    connect_at_init = ''

    if arguments ['--port']:
        connect_at_init += (arguments ['--port'])
    if arguments ['--baud']:
        connect_at_init += (' ' + arguments ['--baud'] )
    if arguments ['--bytesize']:
        connect_at_init += (' ' + arguments ['--bytesize'] )
    if arguments ['--parity']:
        connect_at_init += (' ' + arguments ['--parity'] )
    if arguments ['--stopbits']:
        connect_at_init += (' ' + arguments ['--stopbits'] )
    if arguments ['--sw-flow-ctrl']:
        connect_at_init += (' ' + arguments ['--sw-flow-ctrl'] )
    if arguments ['--hw-rts-cts']:
        connect_at_init += (' ' + arguments ['--hw-rts-cts'] )
    if arguments ['--hw-dsr-dtr']:
        connect_at_init += (' ' + arguments ['--hw-dsr-dtr'] )
    if arguments ['--timeout']:
        connect_at_init += (' ' + arguments ['--timeout'] )

    if 0 < len(connect_at_init):
        shell.do_serial_open(connect_at_init)
    else:
        shell.prompt = shell.PROMPT_DEF

    return shell

def set_debug(debug=False):
    if debug:
        logger.setLevel(logging.DEBUG)

def set_history_length(length):
    rl.set_history_length(length)

def get_history_length():
    length = rl.get_history_length()
    if 0 > length:
        return "No limit"
    return length

def main():
    arguments = docopt(__doc__)
    set_debug(arguments ['-d'] or arguments ['--debug'])

    shell = init(arguments)
    run(shell)

if __name__ == '__main__':
    main()
    #shell = init(arguments)
    #run()


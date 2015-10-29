#!/usr/bin/env python
'''
A Minicom like shell in python
author: Carlo Lobrano

Usage:
    pynicom [-d|--debug] [--port=port --baud=rate --bytesize=bytesize --parity=parity --stopbits=stopbits --sw-flow-ctrl=xonxoff --hw-rts-cts=rtscts --hw-dsr-dtr=dsrdtr --timeout=timeout]

'''
from cmd import Cmd
from docopt import docopt
import glob
import os
import readline
import serial
import sys
from time import sleep

__version__ = "0.1.0"

try:
    import raffaello
    color = True
    patterns = {}
except ImportError:
    color = False

PYTHON3 = sys.version_info > (2.7, 0)

readline.set_completer_delims (' \t\n"\\\'`@$><=;|&{(?+#/%')


arguments = docopt (__doc__, version="0.1.0")

debug = arguments ['-d'] or arguments ['--debug']

if debug:
    print (arguments)


class Pynicom (Cmd):
    STD_BAUD_RATES = ['300', '1200', '2400', '4800', '9600', '19200', '28800', '38400', '57600', '115200', '153600', '2304000', '460800', '500000', '576000', '921600']
    PROMPT_FMT     = '(%s @ %d) '
    PROMPT_DEF     = '(no-conn) '

    commands            = {}
    connection          = None
    last_serial_read    = None
    last_serial_write   = None
    toread              = False
    serial_conf = {'port':'/dev/ttyUSB0', 'baudrate':4800, 'bytesize':8,
            'parity':'N', 'stopbits':1, 'xonxoff':False,
            'rtscts':False, 'dsrdtr':False, 'timeout':1 }
    hist                = set ()


    def do_show_dictionary (self, string = None):
        '''
        If no keyword is provided, it shows all the known commands. If a keyword
        is provided, it shows only matching known commands.
        '''
        if self.__is_string_empty (string):
            logd ('Emtpy search string')
            for name in self.commands:
                log ('%s: %s' % (name, self.commands [name]))
        else:
            matches = [ name for name in self.commands if (string.lower() in name) or (string.lower () in self.commands [name])]
            matches += [ name for name in self.commands if (string.upper() in name) or (string.upper() in self.commands [name])]
            for match in matches:
                log ('%s: %s' % (match, self.commands [match]))


    def do_AT (self, string):
        '''Send AT commands to a connected device'''
        self.do_at (string)


    def complete_AT (self, text, line, begidx, endidx):
        return self.complete_at (text, line, begidx, endidx)


    def do_at (self, string):
        '''Send AT command to a connected device.'''
        if self.__is_valid_connection ():
            self.serial_write ('at%s' % string)


    def complete_at (self, text, line, begidx, endidx):
        #logd ('complete_at: %s, %s, %d, %d' % (text, line, begidx, endidx))
        completions = [key [begidx:] for key in self.commands.keys () if key.lower ().startswith (line.lower ())]
        return completions


    def do_serial_info (self, string=''):
        '''Print out info about the current serial connection'''
        if self.__is_valid_connection ():
            log (self.connection)


    def do_serial_open (self, string):
        '''
        Open the given serial device.

        Example:
        serial_open /dev/ttyUSB0 115200 8 N 1 False False False 1

        where the args are respectively: port, baudrate, bytesize, parity, stopbits, SW flow control, HW flow control RTS/CTS, HW flow control DSR/DTR, timeout
        '''

        for id, arg in enumerate (string.split (' ')):
            if 0 == id:
                self.serial_conf ['port'] = arg
            if 1 == id:
                self.serial_conf ['baudrate'] = arg
            if 2 == id:
                self.serial_conf ['bytesize'] = int (arg)
            if 3 == id:
                self.serial_conf ['parity'] = arg
            if 4 == id:
                self.serial_conf ['stopbits'] = int (arg)
            if 5 == id:
                self.serial_conf ['xonxoff'] = eval (arg)
            if 6 == id:
                self.serial_conf ['rtscts'] = eval (arg)
            if 7 == id:
                self.serial_conf ['dsrdtr'] = eval (arg)
            if 8 == id:
                self.serial_conf ['timeout'] = int (arg)

        logd ('Connecting with the following params {0}.'.format (self.serial_conf))

        try:
            self.connection = serial.Serial (
                    port        = self.serial_conf ['port'],
                    baudrate    = self.serial_conf ['baudrate'],
                    bytesize    = self.serial_conf ['bytesize'],
                    parity      = self.serial_conf ['parity'],
                    stopbits    = self.serial_conf ['stopbits'],
                    xonxoff     = self.serial_conf ['xonxoff'],
                    rtscts      = self.serial_conf ['rtscts'],
                    dsrdtr      = self.serial_conf ['dsrdtr'],
                    timeout     = self.serial_conf ['timeout']
                    )

        except (ValueError, serial.SerialException) as err:
            loge (err)

        if self.__is_valid_connection ():
            self.prompt = self.__set_prompt ()

    def complete_serial_open (self, text, line, begidx, endidx):
        nargs = len (line.split (' '))

        if 2 == nargs:
            completions = self.complete_set_port (text, line, begidx, endidx)

        elif 3 == nargs:
            completions = self.complete_set_baudrate (text, line, begidx, endidx)

        elif 5 == nargs:
            completions = self.complete_set_parity (text, line, begidx, endidx)

        else:
            completions = []

        return completions


    def do_set_port (self, string):
        '''Set serial device fullpath for the connection'''
        if self.__is_valid_connection ():
            try:
                self.connection.port = string
                self.prompt = self.__set_prompt ()
            except (serial.serialutil.SerialException) as err:
                logd (err)


    def complete_set_port (self, text, line, begidx, endidx):
        before_arg = line.rfind (" ", 0, begidx)

        if -1 == before_arg:
            return # arg not found

        fixed   = line [before_arg + 1 : begidx]  # fixed portion of the arg
        arg     = line [before_arg + 1 : endidx]
        pattern = arg + '*'

        return [path.replace (fixed, "", 1) for path in glob.glob (pattern)]


    def do_set_baudrate (self, string):
        '''Set connection baud rate'''
        if self.__is_valid_connection ():
            self.connection.baudrate = string
            self.prompt = self.__set_prompt ()


    def complete_set_baudrate (self, text, line, begidx, endidx):
        token = line [begidx : endidx + 1]
        return [rate for rate in self.STD_BAUD_RATES if rate.startswith (token)]


    def do_set_bytesize (self, string):
        '''Set serial connection bytesize'''
        if self.__is_valid_connection ():
            self.connection.bytesize = int (string)


    def do_set_parity (self, string):
        '''Set serial connection parity'''
        if self.__is_valid_connection ():
            self.connection.parity = string

    def complete_set_parity (self, text, line, begidx, endidx):
        return ['N' 'O']


    def do_set_stopbits (self, string):
        '''Set serial connection stopbits'''
        if self.__is_valid_connection ():
            self.connection.stopbits = int (string)


    def do_set_timeout (self, string):
        '''Set serial connection timeout'''
        if self.__is_valid_connection ():
            self.connection.timeout = int (string)


    def do_serial_read (self, string = ''):
        '''
        Read from serial device. Press CTRL-C to interrupt it
        '''
        stop_read_counter = 3
        while stop_read_counter > 0 or 'nostop' in string:
            try:
                if not PYTHON3:
                    logd ('reading without decode')
                    read = self.connection.readline ().rstrip ()
                else:
                    logd ('reading with decode')
                    read = self.connection.readline ().decode ().rstrip ()

                logd ('got "%s"' % read)

                if self.__is_echo (read):
                    logd ('Got echo (%s)' % read)
                    continue

                if len (read):
                    if None != self.last_serial_write and self.last_serial_write.lower () != 'at' and 'OK' == read:
                        continue
                    else:
                        self.last_serial_read = read
                        log ('%s%s' % (' '*len(self.prompt), read))
                elif 0 < stop_read_counter:
                    logd ('stop read counter %d' % stop_read_counter)
                    stop_read_counter -= 1
                    continue
                else:
                    logd ("Nothing to read, exiting")
                    break

            except (OSError,serial.serialutil.SerialException) as error:
                loge ("Got SerialException/OSerror (%d)" % stop_read_counter);
                loge (error)
                stop_read_counter -= 1
            except KeyboardInterrupt:
                log ('Keyboard interrupt')
                break


    def complete_serial_read (self, text, line, begidx, endidx):
        return ['nostop']


    def do_history (self, string):
        for cmd in self.hist:
            log (cmd)


    def preloop (self):
        Cmd.preloop (self)

        if os.path.exists ('./history.txt'):
            logd ('Reading history')
            commands = [line for line in open ('./history.txt', 'r').readlines () if len (line)]
            self.hist = set (commands)


    def postloop (self):
        self.save_history ()
        Cmd.postloop (self)


    def save_history (self):
        logd ('Saving history...')
        if 0 < len (self.hist):
            history = open ('./history.txt', 'a')
            for cmd in self.hist:
                history.write (cmd + '\n')


    def precmd (self, line):
        if len (line):
            logd ('Add %s to history' % line.strip ())
            self.hist.add (line.strip ())
        return line


    def postcmd (self, stop, line):
        if self.toread:
            self.do_serial_read ('')
            self.toread = False

        return stop


    def do_serial_close (self, string=''):
        '''Close serial connection (if any)'''

        if self.__is_valid_connection ():
            self.connection.close ()
            self.prompt = self.PROMPT_DEF
            self.serial_conf = {'port':'/dev/ttyUSB0', 'baudrate':4800, 'bytesize':8,
            'parity':'N', 'stopbits':1, 'xonxoff':False,
            'rtscts':False, 'dsrdtr':False, 'timeout':1 }
            log ('connection closed')


    def do_exit (self, string=''):
        '''Exit from Pynicom shell'''
        self.do_serial_close ()
        sys.exit (0)


    def do_quit (self, string=''):
        '''Exit from Pynicom shell'''
        self.do_serial_close ()
        sys.exit (0)


    def do_shell (self, cmd):
        os.system (cmd)


    def do_help (self, string = ''):
        logd ('help for %s' % string)

        if (string.upper () in self.commands.keys ()):
            print ('\t%s' % self.commands [string.upper ()])

        elif (string.lower () in self.commands.keys ()):
            print ('\t%s' % self.commands [string.lower ()])

        else:
            Cmd.do_help(self, string)

    def do_set_debug (self, string):
        '''
        Enable/Disable debug
        e.g.
            set_debug False
            set_debug True
        '''
        global debug
        debug = eval (string)

    def complete_set_debug (self, text, line, begidx, endidx):
        completions = ['False', 'True']


    def do_nmea (self, string):
        sentence = self.__nmea_format (string)
        log ('nmea > "$%s<CR><LF>"' % sentence)
        self.serial_write ('$' + sentence, appendix = '\r\n')


    def complete_nmea (self, text, line, begidx, endidx):
        custom_msg = ['PMTK', 'PSRF']
        if 0 >= len (text):
            return custom_msg
        else:
            return [cmd for cmd in custom_msg if cmd.startswith (text.upper ())]


    def default (self, line):
        self.__send_raw (line)


    def emptyline (self):
        '''
        Default emptyline will repeat last command, while usually that is not
        the expected behavior in a Shell
        '''
        pass


    def serial_write (self, msg, appendix='\r'):
        try:
            msg_cr = msg + appendix
            logd ('sending: "%s"' % repr(msg_cr))
            if not PYTHON3:
                logd ('No encode')
                bytes = self.connection.write (msg_cr)
                logd ("wrote %d bytes" % bytes)
            else:
                logd ('encode')
                bytes = self.connection.write (msg_cr.encode ())

            if 0 >= bytes:
                logd ('Wrote %d bytes' % bytes)
            else:
                self.last_serial_write = msg
                self.toread = True

        except (TypeError) as err:
            loge ('Could not write msg "%s": %s' % (msg, err))


    def __is_valid_connection (self):
        logd ('check connection')
        retval = True
        if (None == self.connection) or (not self.connection.isOpen ()):
            log ('No serial connection established yet')
            retval = False
        return retval


    def __send_raw (self, string=''):
        '''Let the user send raw messages to the serial device'''
        if self.__is_valid_connection ():
            self.serial_write (string)


    def __is_string_empty (self, string):
        return (None == string or 0 == len (string))


    def __is_echo (self, string):
        retval = (string == self.last_serial_write)
        return retval


    def __set_prompt (self):
        logd (self.connection.baudrate)
        return self.PROMPT_FMT % (self.connection.port, self.connection.baudrate)


    def __nmea_format (self, message):
        checksum = self.__nmea_checksum (message)
        well_formed_message = '%s*%s' % (message, checksum)
        return well_formed_message


    def __nmea_checksum (self, message):
        checksum = 0

        for c in message:
            checksum ^= ord (c)

        return '%02X' % checksum

    def do_highlight (self, string):
        if color:
            global patterns
            try:
                new_entry = raffaello.parse_color_option (string)
                patterns.update (new_entry)
            except Exception as err:
                loge ('Could not highlight "%s". Error %s' % (string, err))

        else:
            loge ('Highlightning not available. Raffaello module not found')


    def do_show_highlight (self, string):
        if color:
            global patterns
            log (patterns)
        else:
            loge ('Highlightning not available. Raffaello module not found')


    def do_remove_highlight (self, string):
        if color:
            global patterns
            if string in patterns.keys ():
                del patterns [string]
            else:
                log ('Pattern "%s" is not highlighted' % string)
        else:
            loge ('Highlightning not available. Raffaello module not found')






def get_commands (string_list):
    if 0 == len (string_list):
        loge ('No data to generate known command list')
        return

    commands = {}
    at_cmd = None
    at_cmd_doc = ''
    for string in string_list:
        if 0 == len (string):
            continue

        logd ('-- Parsing %s' % string.rstrip ())
        if string.lower ().startswith ('at'):

            if None != at_cmd and 0 != len (at_cmd_doc):
                logd ('Adding doc %s to %s' % (at_cmd_doc, at_cmd))
                commands [at_cmd] = at_cmd_doc
                at_cmd_doc = ''

            else:
                logd ('No doc to update (at_cmd: {0}, at_cmd_doc {1})'.format (at_cmd, at_cmd_doc))

            short_help = 'no help found'
            if (' # ' in string) or (' #' in string):
                logd ('Inline short help found')
                string, short_help = string.split (' # ')
                logd (string)

            at_cmd = string.strip ()
            at_key = string [2]
            cmd = string [3:].strip ()

            logd ('adding %s to dict for at%s' % (at_cmd, at_key))
            commands [at_cmd] = short_help.rstrip ()

        if string.startswith ('#'):
            logd ('Got doc for at cmd %s' % at_cmd)
            at_cmd_doc += string [1:]   # skip initial '#'

    return commands


def stub_do_func (instance, string):
    if (None == instance.connection) or (not instance.connection.isOpen ()):
       log ('No serial connection established yet')
    else:
        cmd = '%s' % string
        instance.serial_write (cmd)


def contains_symbols (string, symbols):
    set_sym = set (symbols)
    set_str = set (string)

    retval = (0 != len (set_sym.intersection (set_str)))
    logd ('{0} contains {1}? {2}'.format (string, set_sym, retval))

    return retval


def add_do_command (commands, cls):
    for cmd in commands.keys ():
        if not contains_symbols (cmd, '+%&$\#/'):
            logd ("Adding %s" % cmd)
            setattr (cls, 'do_%s' % cmd, stub_do_func)

            if cmd.isupper ():
                setattr (cls, 'do_%s' % cmd.lower (), stub_do_func)
            else:
                setattr (cls, 'do_%s' % cmd.upper (), stub_do_func)






def logd (msg):
    if debug:
        print (' [D] %s' % msg)

def logi (msg):
    print (' [I] %s' % msg)

def loge (msg):
    print (' [E] %s' % msg)

def logw (msg):
    print (' [W] %s' % msg)

def log (msg):
    if color:
        print (raffaello.paint ('%s' % msg, patterns))
    else:
        print ('%s' % msg)




def init (arguments = {}):
    known_commands = get_commands (open ('./dictionary.txt', 'r').readlines ())
    add_do_command (known_commands, Pynicom)

    shell = Pynicom ()

    shell.commands = known_commands
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

    if 0 < len (connect_at_init):
        shell.do_serial_open (connect_at_init)
    else:
        shell.prompt = shell.PROMPT_DEF

    return shell

def run ():
    try:
        shell.cmdloop (__doc__)
    except KeyboardInterrupt:
        shell.save_history ()
        logi ("Keyboard interrupt")

    if None != shell.connection and shell.connection.isOpen ():
        shell.do_serial_close ('')


def main ():
    shell = init (arguments)
    run ()


if __name__ == '__main__':
    shell = init (arguments)
    run ()


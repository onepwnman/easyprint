import os
import re
import sys
import random
import hashlib
import RPi.GPIO as gpio
import serial
import glob
import logging
import threading
import queue
import time
import logging

from flask import Blueprint, flash, current_app
from rq import get_current_job, job

printer = Blueprint('printer', __name__)


class TestPrinter(object):
    def __init__(self):
        self.infill = ''
        self.layer_height = ''
        self.total_layer = 0
        self.current_layer = 0
        self.filament_used = ''

        
    def print_model(self, dummy):
        time.sleep(5)
        self.total_layer = 200
        for i in range(self.total_layer):
            self.current_layer = i
            random_time = round(random.random())
            time.sleep(random_time)

        self.filament_used = '1.31m'
        self.infill = '20'
        self.layer_height = '0.2'
        time.sleep(3)


class Printer(object):
    def __init__(self):
        self.power_pin = 16
        self.baudrate = 115200
        self.power_on = False
        self.timeout = 1
        self.default_timeout = 1
        self.printing_timeout = self.default_timeout
        self.leveling_timeout = 30
        self.heating_up_timeout = 600
        self.timeout_flag = False
        self.STATE_NONE = 0
        self.STATE_PRINTER_POWER_OFF = 1
        self.STATE_PRINTER_POWER_ON = 2
        self.STATE_SERIAL_CONNECTED = 3
        self.STATE_HEATING_UP = 4
        self.STATE_LEVELING = 5
        self.STATE_PRINTING = 6
        self.state = self.STATE_PRINTER_POWER_OFF
        self.line_number = 1
        self.retry_count = 0
        self.logger = logging.getLogger(__name__)
        self.command_history_buffer = {}
        self.MAX_RETRY_COUNT = 20
        self.command_queue_size = 300
        self.command_queue = queue.Queue(maxsize=self.command_queue_size)
        self.filament_used = ''
        self.infill = ''
        self.layer_height = ''
        self.total_layer = 0
        self.current_layer = 0
        self.PRINT_END_MARK = 'PRINT DONE!'

    
    def __del__(self):
        self.serial.close()
        self.power_off()
        

    def power_on(self):
        # Take some time
        if self.state == self.STATE_PRINTER_POWER_OFF:
            gpio.setmode(gpio.BCM)
            gpio.setup(self.power_pin, gpio.OUT)
            gpio.output(self.power_pin, False)
            self.state = self.STATE_PRINTER_POWER_ON
            time.sleep(1)


    def power_off(self):
        # It's ok to close twice
        self.serial.close() 
        if self.state != self.STATE_PRINTER_POWER_OFF:
            gpio.setmode(gpio.BCM)
            gpio.setup(self.power_pin, gpio.IN)
            time.sleep(1)

    
    def connect(self):
        try:
            self.port = glob.glob('/dev/ttyUSB*')[0]
            self.serial = serial.Serial( self.port,
                                        baudrate=self.baudrate,
                                        timeout=self.timeout,
                                        )
            while self.serial.in_waiting == 0:
                pass
        except IndexError:
            self.logger.error('Please Check the USB Connection.')
            return False
        except serial.SerialException:
            self.logger.error('Somethings wrong while connecting serial port.')
            return False
        return True 


    def boot_up(self):
        self.power_on()
        if self.connect():
            self.send_command('M117 Hello Printer!')
            self.logger.info('Ready for print.')
            self.state = self.STATE_SERIAL_CONNECTED

            
    def clean_up(self):
        self.serial.close()
        self.power_off()
        

    def send_with_checksum(self, command, linenumber):
        linenumbered_command = "N" + str(linenumber) + " " + command
        checksum = 0
        for c in bytearray(linenumbered_command, 'utf-8'):
            checksum ^= c

        linenumbered_command = linenumbered_command + "*" + str(checksum)
        self.send_command(linenumbered_command)
        

    def critical_error(self, message):
        self.logger.error(message)
        self.power_off()


    def resend(self):
        if self.retry_count <= self.MAX_RETRY_COUNT:
            self.logger.info('retry count: {}'.format(self.retry_count))
            resend_line = self.serial.readline().decode()
            resend_line_number_pattern = re.compile('Resend\: ([0-9]*)')
            resend_line_number = resend_line_number_pattern.search(resend_line).group(1)
            self.line_number = int(resend_line_number)
            final_line = self.serial.readline().decode()

            if final_line.startswith('ok'):
                self.retry_count += 1
                try:
                    self.send_with_checksum(self.command_history_buffer[int(resend_line_number)],
                                          resend_line_number)
                except KeyError:
                    self.critical_error('command not in the history yet')
            else:
                self.critical_error('Somthings wrong!')
        else:
            self.critical_error('Exceed retry count!')


    def send_command(self, cmd):
        cmd += '\n'
        self.logger.info('Sending Command: {}'.format(cmd))
        try:
            self.serial.write(cmd.encode())
        except serial.serialutil.SerialException:
            self.connect()
            self.send_command('M117 Hello Printer!')
            self.logger.info('reconnected!')
            self.serial.write(cmd.encode())

        while True:        
            line = self.serial.readline().decode()
            if line != '':
                self.logger.info(line)
            if line == '':
                if self.timeout_flag is True:
                    # Timeout Occurrued
                    line = 'ok\n'
                    self.logger.info('Send ok and continue next command')
                    self.serial.reset_input_buffer()
                    self.timeout_flag = False
                else:
                    continue

            if line.startswith('ok'):
                self.retry_count = 0
                break
            elif line.startswith('Error:'):
                line_number_pattern = re.compile('Error\:Line Number is not Last Line Number\+1, Last Line\: ([0-9]*)\n')
                try:
                    self.logger.error('line number mismatch')
                    # line number mismatch error
                    self.resend()
                    break
                    
                except AttributeError:
                    # checksum error
                    checksum_pattern = re.compile('Error\:checksum mismatch, Last Line\: ([0-9]*)\n', re.S)
                    try:
                        self.logger.error('checksum mismatch')
                        self.resend()
                        break
                      
                    except AttributeError:
                        self.critical_error('Unknown Error')
                      
                except:
                    self.critical_error('Unknown Error')
                
            
    def halt(self):
        self.send_command('M112')


    def print_model(self, gcode_file):
        from ..main import app

        def get_line_from_file(gcode_file):
            def get_number(l):
                return l.split(':')[1]

            #  try:
            with open(gcode_file, 'rt') as f:
                for line in f:
                    line = line.strip('\n')
                    if line == '':
                        continue
                    if line.startswith(';'):
                        # meta info in gcode file
                        # ;FLAVOR: Marlin
                        # ;TIME: 
                        # ;Filament userd:
                        # ;Layer height: 
                        # ;MINX:
                        # ;MINY:
                        # ;MINZ:
                        # ;MAXX:
                        # ;MAXY:
                        # ;MAXZ:
                        # ;LAYER_COUNT:
                        # ;LAYER:
                        # ;INFILL: 
                        line = line.lstrip(';')
                        if line.startswith('LAYER_COUNT'):
                            self.total_layer = int(get_number(line))
                        elif line.startswith('LAYER'):
                            self.current_layer = int(get_number(line))
                            app.logger.debug('Current layer: {}'.format(self.current_layer))
                        elif line.startswith('Filament used'):
                            self.filament_used = get_number(line)
                        elif line.startswith('INFILL'):
                            self.infill = get_number(line)
                        elif line.startswith('Layer height'):
                            self.layer_height = get_number(line)
                        elif line.startswith('End of Gcode'):
                            self.command_queue.put(self.PRINT_END_MARK)
                            break
                        continue
                    # Get rid of trailing comment
                    if ';' in line:
                        line = line[:line.index(';')]
                    
                    self.command_queue.put(line)


        def send_from_queue():
            while True:
                # We don't need lock
                cmd = self.command_queue.get()

                if cmd == self.PRINT_END_MARK:
                    break
                elif cmd.startswith('M105'):       # Temperature report command
                    timeout = self.heating_up_timeout
                elif cmd.startswith('G28') or cmd.startswith('G29'):
                    timeout = self.leveling_timeout
                else:
                    timeout = self.printing_timeout
                self.serial.timeout = timeout

                def _setter():
                    self.timeout_flag = True
                threading.Timer(timeout, _setter).start()
        
                self.command_history_buffer[self.line_number] = cmd
                self.send_with_checksum(cmd, self.line_number)
                self.line_number += 1

                self.command_queue.task_done() 

      
        self.boot_up()
        self.state = self.STATE_PRINTING

        # Sometime you can't get '\n' in the input buffer when marlin firmware is connected
        # Sending several dummy commands would work
        for i in range(10):
            self.send_command('M117 Hello Printer!')

        parser = threading.Thread(target=get_line_from_file, args=(gcode_file,))
        consumer = threading.Thread(target=send_from_queue)
        parser.start()
        consumer.start()
        consumer.join()
        self.logger.info('Printing Finished!')
        self.clean_up()



def upload_file(file):
    allowed_extensions = {
                          'stl',
    }
    
    def verify_file(_file):
        if _file and len(_file.filename) <= current_app.config['ALLOWED_FILE_NAME_LENGTH']:

            # Check file name has valid extension 
            if '.' in _file.filename:
                extension = _file.filename.rsplit('.')[-1]
                if extension.lower() in allowed_extensions:
                  
                    # File should be validated not only by the name 
                    # But also from the binary level
                    return True

        return False

    def generate_random_filename():
        hash = hashlib.sha1(os.urandom(64))
        return str(hash.hexdigest()) + '.stl'

    if verify_file(file):
        save_filename = generate_random_filename()
        save_file_fullpath = current_app.config['UPLOAD_FOLDER'] + save_filename
        file.save(save_file_fullpath)
        return save_file_fullpath.split(current_app.config['BASEDIR'])[-1].split('src')[1]
    else:
        return None



from . import views



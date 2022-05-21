#!/usr/bin/env python
###-------------------------------------------------------------------------
### Mojo.py is a bitstream uploader for the mojo v2 board
### author    Matthew O'Gorman <mog@rldn.net>
### copyright 2013 Matthew O'Gorman
### version 2.0
### ### License : This program is free software, distributed under the terms of
###           the GNU General Public License Version 3. See the COPYING file
###           at the top of the source tree.
###-------------------------------------------------------------------------

import time
import sys
import argparse
import serial
import struct
#Try to rename process to something more friendly than python mojo.py
try:
    import setproctitle
    setproctitle.setproctitle('mojo')
except ImportError as error:
    pass

def main():
    Version = "Mojo v2.0 is licensed under the GPLv3 copyright 2013 Matthew O'Gorman"

    parser = argparse.ArgumentParser(description='Mojo bitstream loader v2')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('bitstream', metavar='BITSTREAM', nargs='?',
                        help='Bitstream file to upload to the Mojo.')
    group.add_argument('-i', '--install', metavar='BITSTREAM', dest='install', action='store',
                       help='Bitstream file to upload to the Mojo')
    parser.add_argument('-r', '--ram', dest='ram', action='store_const',
                       const=True, default=False,
                       help='Install bitstream file only to ram')
    #not currently supported by the default firmware of the board
    # group.add_argument('-c', '--copy', metavar='BITSTREAM', dest='copy', action='append', nargs='?',
    #                     help='Bitstream file to copy from the Mojo [Default: %(default)s]', default=['mojo.bin'])

    # group.add_argument('-o', '--only_verify', metavar='BITSTREAM', dest='only_verify', action='store',
    #                    help='Read flash of Mojo only to verify against bitstream.')
    # group.add_argument('-r', '--reboot', dest='reboot', action='store_const',
    #                    const=True, default=False,
    #                    help='Reboot mojo board.')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_const',
                       const=True, default=False,
                       help='Enable verbose output to cli.')
    parser.add_argument('-V', '--version', dest='version', action='store_const',
                       const=True, default=False,
                       help='Display version number of mojo.')
    parser.add_argument('-n', '--no-verify', dest='no_verify', action='store_const',
                       const=True, default=False,
                       help='Do not verify the operation to the Mojo.')
    group.add_argument('-e', '--erase', dest='erase', action='store_const',
                       const=True, default=False,
                       help='Erase flash on Mojo.')
    parser.add_argument('-d', '--device', dest='mojo_tty', action='store',
                       default='/dev/mojo',
                        help='Address of the serial port for the mojo [Default: %(default)s]')
    parser.add_argument('-p', '--progress', dest='progress', action='store_const',
                        const=True, default=False,
                        help='Display progress bar while uploading.')

    args = parser.parse_args()

    if args.version:
        print(Version)
        sys.exit(0)

    #Serial code
    try:
        ser = serial.Serial(args.mojo_tty, 19200, timeout=20)
    except:
        print('No serial port found named ' + args.mojo_tty)
        sys.exit(1)

#    if (not args.bitstream and  not args.install and not args.copy and not args.erase and not args.only_verify and not args.reboot):
    if (not args.bitstream and  not args.install and not args.erase):
        print(parser.print_help())
        sys.exit(1)
    if args.erase:
        if args.verbose:
            print("Preparing to erase")
        erase_mojo(ser, args.verbose)
        sys.exit(0)
    if args.bitstream:
        install_mojo(ser, args.bitstream, args.verbose, args.no_verify, args.ram, args.progress)
        sys.exit(0)
    if args.install:
        install_mojo(ser, args.install, args.verbose, args.no_verify, args.ram, args.progress)
        sys.exit(0)

def display_progress(p, prefix='', width=40):
    if p > 1:
        p = 1
    if p < 0:
        p = 0
    bar_width = int(width * p)
    rem_bar_width = int(width - bar_width)
    arrow = '>' if p < 1 else '='
    sys.stdout.write("\r" + prefix + "[" + ("=" * (bar_width-1)) + arrow + (" " * rem_bar_width) +
                     ("] (%d%%)" % int(100 * p)))
    sys.stdout.flush()

def install_mojo(ser, bitstream, verbose, no_verify, ram, progress):
    CHUNK_SIZE = 4096
    file = open(bitstream, 'rb')
    bitstream = file.read()
    length = len(bitstream)
    reboot_mojo(ser, verbose)

    if ram:
        ser.write(b'R')
        ret = ser.read(1)
        if verbose and  ret == b'R':
            print('Mojo is ready to recieve bitstream')
        elif ret != b'R':
            print('Mojo did not respond correctly! Make sure the port is correct', ret)
            sys.exit(1)

    if not ram and no_verify:
        ser.write(b'F')
        ret = ser.read(1)
        if verbose and  ret == b'R':
            print('Mojo is ready to recieve bitstream')
        elif ret != b'R':
            print('Mojo did not respond correctly! Make sure the port is correct', ret)
            sys.exit(1)

    if not ram and not no_verify:
        ser.write(b'V')
        ret = ser.read(1)
        if verbose and  ret == b'R':
            print('Mojo is ready to recieve bitstream')
        elif ret != b'R':
            print('Mojo did not respond correctly! Make sure the port is correct', ret)
            sys.exit(1)

    buffer = struct.unpack("4B", struct.pack("I", length))
    ser.write(buffer)
    ret = ser.read(1)
    if verbose and ret == b'O':
        print('Mojo acknowledged size of bitstream.')
    elif ret != b'O':
        print('Mojo failed to acknowledge size of bitstream. Did not write', ret)
        sys.exit(1)

    if progress:
        sent_len = 0
        bits = bitstream
        while len(bits) > 0:
            chunk_len = CHUNK_SIZE if (len(bits) >= CHUNK_SIZE) else len(bits)
            chunk = bits[0:chunk_len]
            bits = bits[chunk_len:]
            write_len = ser.write(chunk)
            if (write_len != chunk_len):
                print('Failed to write complete chunk: ({}/{})'.format(write/chunk_len))
            sent_len += chunk_len
            display_progress(float(sent_len)/length, prefix='  Writing Bitstream ')
        sys.stdout.write('\n')
    else:
        print('Writing Bitstream...')
        ser.write(bitstream)

    ret = ser.read(1)
    if verbose and ret == b'D':
        print('Mojo has been flashed')
    elif ret != b'D':
        print('Mojo failed to flash correctly', ret)
        sys.exit(1)

    if not ram and not no_verify:
        ser.write(b'S')
        if verbose:
            print('Verifying Mojo')
        ret = ser.read(1)
        if ret == b'\xAA' and verbose:
            print('First Byte was valid getting flash size.')
        elif ret != b'\xAA':
            print('Flash does not contain valid start byte.', ret)
            sys.exit(1)
        ret = ser.read(4)
        flash_length = struct.unpack("I", ret)[0] - 5
        if flash_length == length and verbose:
            print('Flash and local bitstream match file size.')
        elif flash_length != length:
            print('Flash is not same size as local bitstream.')
            sys.exit(1)

        if progress:
            recv_len = 0
            ret = b''
            while recv_len < length:
                chunk_len = CHUNK_SIZE if ((length - recv_len) >= CHUNK_SIZE) else (length - recv_len)
                chunk = ser.read(chunk_len)
                ret += chunk
                recv_len += len(chunk)
                display_progress(float(recv_len)/length, prefix='Verifying Bitstream ')
            sys.stdout.write('\n')
        else:
            print('Verifying Bitstream...')
            ret = ser.read(length)

        valid = (ret == bitstream)
        if valid and verbose:
            print('Flash and local bitstream are a match.')
        elif not valid:
            print('Flash and local bitstream do not match.')
            with (open('verify_failure.bin', 'wb') as of):
                of.write(ret)
            sys.exit(1)
    if not ram:
        ser.write(b'L')
        ret = ser.read(1)
        if verbose and ret == b'D':
            print('Mojo has loaded bitsream')
        elif ret != b'D':
            print('Mojo failed to load bitstream', ret)
            sys.exit(1)
    return

def reboot_mojo(ser, verbose):
    ser.setDTR(True)
    time.sleep(0.005)
    for i in range(0,5):
        ser.setDTR(False)
        time.sleep(0.005)
        ser.setDTR(True)
        time.sleep(0.005)
    if verbose:
        print('Rebooting Mojo')
    return

def erase_mojo(ser, verbose):
    reboot_mojo(ser, verbose)
    ser.write(b'E')
    ret = ser.read(1)
    if verbose and ret == b'D':
        print('Erased mojo successfully.')
    elif ret != b'D':
        print('Failed to erase Mojo.  Error code: ' + ret)
        sys.exit(1)
    ser.close()
    sys.exit(0)
    return


main()

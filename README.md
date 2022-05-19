# mojo.py
Command line bitstream uploader for the Mojo FPGA board.

# Usage
```
usage: mojo.py [-h] [-i BITSTREAM] [-r] [-v] [-V] [-n] [-e] [-d MOJO_TTY] [-p] [BITSTREAM]

Mojo bitstream loader v2

positional arguments:
  BITSTREAM             Bitstream file to upload to the Mojo.

options:
  -h, --help            show this help message and exit
  -i BITSTREAM, --install BITSTREAM
                        Bitstream file to upload to the Mojo
  -r, --ram             Install bitstream file only to ram
  -v, --verbose         Enable verbose output to cli.
  -V, --version         Display version number of mojo.
  -n, --no-verify       Do not verify the operation to the Mojo.
  -e, --erase           Erase flash on Mojo.
  -d MOJO_TTY, --device MOJO_TTY
                        Address of the serial port for the mojo [Default: /dev/mojo]
  -p, --progress        Display progress bar while uploading.
```

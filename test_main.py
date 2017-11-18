""" This module contains some tests of code functionality. """

import logging
import time
from src import dolphincontroller, keylog, basicMarioKartdownsampler

# Configure logger
logging.basicConfig(format='%(name)s:%(filename)s:%(lineno)d:%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dolphin_controller():
    """ Check that the Dolphin controller can communicate with Dolphin using a fifo pipe. """
    with dolphincontroller.DolphinController("~/.dolphin-emu/Pipes/pipe") as p:
        p.press_release_button(dolphincontroller.Button.START, delay=0.1)
        time.sleep(0.1)

def test_basic_Mario_Kart_downsampler():
    """ Check that the basic Mario Kart image downsampler can process images saved by Dolphin. """
    basicMarioKartdownsampler.Downsampler('NABE01', final_dim=15).downsample_dir(save_imgs=True)

def test_key_logging():
    """ Check that keyboard input can be successfully logged to a .json file. """
    k = keylog.KeyLog()
    k.start()


# Main function for entering tests
def main():
    test_key_logging()


if __name__ == '__main__':
    main()
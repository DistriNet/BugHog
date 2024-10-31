import base64
import os
from io import BytesIO
from time import sleep

import pyautogui as gui
import Xlib.display
from pyvirtualdisplay.display import Display

from bci.browser.configuration.browser import Browser as BrowserConfig


class Browser:
    browser_config: BrowserConfig
    public_methods: list[str] = ['navigate', 'click']

    def __init__(self, browser_config: BrowserConfig):
        self.browser_config = browser_config
        disp = Display(visible=True, size=(1920, 1080), backend='xvfb', use_xauth=True)
        disp.start()
        gui._pyautogui_x11._display = Xlib.display.Display(os.environ['DISPLAY'])

    def __del__(self):
        self.browser_config.terminate()

    # --- PUBLIC METHODS ---
    def navigate(self, url: str):
        self.browser_config.terminate()
        self.browser_config.open(url)

        # TODO - convert this into an argument or a separate command
        sleep(0.5)

    def click(self, x: str, y: str):
        # print(gui.size())
        # print(gui.position())
        # gui.moveTo(int(x), int(y))
        gui.moveTo(100, 540)
        gui.click()

        # buffered = BytesIO()
        # print(gui.screenshot().save(buffered, format='JPEG'))
        # img_str = base64.b64encode(buffered.getvalue())
        # print(img_str.decode('utf-8'))

        sleep(0.5)

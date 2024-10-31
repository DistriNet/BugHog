import base64
import os
from io import BytesIO
from time import sleep

import pyautogui as gui
import Xlib.display
from pyvirtualdisplay.display import Display

from bci.browser.configuration.browser import Browser as BrowserConfig


class Simulation:
    browser_config: BrowserConfig
    public_methods: list[str] = ['navigate', 'click', 'sleep']

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

    def click(self, x: str, y: str):
        gui.moveTo(100, 540)
        gui.click()

    def sleep(self, duration: str):
        sleep(float(duration))

    def screenshot(self):
        # TODO
        # buffered = BytesIO()
        # print(gui.screenshot().save(buffered, format='JPEG'))
        # img_str = base64.b64encode(buffered.getvalue())
        # print(img_str.decode('utf-8'))
        pass

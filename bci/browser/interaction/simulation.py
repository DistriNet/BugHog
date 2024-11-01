import os
from time import sleep

import pyautogui as gui
import Xlib.display
from pyvirtualdisplay.display import Display

from bci.browser.configuration.browser import Browser as BrowserConfig
from bci.evaluations.logic import TestParameters


class Simulation:
    browser_config: BrowserConfig
    params: TestParameters

    public_methods: list[str] = [
        'navigate',
        'click_position',
        'click',
        'write',
        'press',
        'hold',
        'release',
        'hotkey',
        'sleep',
        'screenshot',
    ]

    def __init__(self, browser_config: BrowserConfig, params: TestParameters):
        self.browser_config = browser_config
        self.params = params
        disp = Display(visible=True, size=(1920, 1080), backend='xvfb', use_xauth=True)
        disp.start()
        gui._pyautogui_x11._display = Xlib.display.Display(os.environ['DISPLAY'])

    def __del__(self):
        self.browser_config.terminate()

    def parse_position(self, position: str, max_value: int) -> int:
        # Screen percentage
        if position[-1] == '%':
            return round(max_value * (int(position[:-1]) / 100))

        # Absolute value in pixels
        return int(position)

    # --- PUBLIC METHODS ---
    def navigate(self, url: str):
        self.browser_config.terminate()
        self.browser_config.open(url)
        self.sleep('0.5')

    def click_position(self, x: str, y: str):
        max_x, max_y = gui.size()

        gui.moveTo(self.parse_position(x, max_x), self.parse_position(y, max_y))
        gui.click()

    def click(self, el_id: str):
        el_image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'elements/{el_id}.png')
        x, y = gui.locateCenterOnScreen(el_image_path)
        self.click_position(str(x), str(y))

    def write(self, text: str):
        gui.write(text, interval=0.1)

    def press(self, key: str):
        gui.press(key)

    def hold(self, key: str):
        gui.keyDown(key)

    def release(self, key: str):
        gui.keyUp(key)

    def hotkey(self, *keys: str):
        gui.hotkey(*keys)

    def sleep(self, duration: str):
        sleep(float(duration))

    def screenshot(self, filename: str):
        filename = f'{self.params.evaluation_configuration.project}-{self.params.mech_group}-{filename}-{type(self.browser_config).__name__}-{self.browser_config.version}.jpg'
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../logs/screenshots', filename)
        gui.screenshot(filepath)

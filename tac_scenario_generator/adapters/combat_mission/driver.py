import logging
from datetime import datetime
from enum import Enum

# TODO: if we stick with easyOCR, we should archive the model weights with this
# project so that it's reproducible even if EasyOCR changes in the future.
import easyocr
import pyautogui
from thefuzz import fuzz
from thefuzz import process as fuzz_process

from tac_scenario_generator.settings import SCREENSHOTS_DIR
from tac_scenario_generator.adapters.combat_mission.errors import ScreenStateError

logger = logging.getLogger(__name__)


class CombatMissionDriver():
    """ABC for drivers which manage the state of and interactions with the
    CombatMission game process. Notice that there is some handling of subtle
    differences between the games baked directly into the methods of this
    class. CMBO (Combat Mission Beyond Overlord) has the most significant
    differences from the other two.
    """
    def __init__(self, game_id):
        self._current_screen = Screen.SCENARIO_EDITOR
        self._game_id = game_id

    def go_to_unit_editor(self):
        if self._current_screen is not Screen.SCENARIO_EDITOR:
            raise ScreenStateError(
                'Driver does not yet support navigating to Unit Editor screen except '
                'from Scenario Editor screen. Current screen is {current_screen.name}.'
            )
        if self._game_id == 'cmbo':
            text = 'UNITS'
        else:
            text = 'UNIT'  #EasyOCR doesn't merge "UNIT EDITOR", so we just target the top, unique word.
        self.click_target_text(text)
        self._current_screen = Screen.UNIT_EDITOR

    def go_to_scenario_editor(self):
        if self._current_screen is not Screen.UNIT_EDITOR:
            raise ScreenStateError(
                'Driver does not yet support navigating to Scenario Editor screen except '
                'from Unit Editor screen. Current screen is {current_screen.name}.'
            )
        self.click_target_text('OK')
        self._current_screen = Screen.SCENARIO_EDITOR

    # TODO: reconsider all of the below functions, and get them above this line or delete them

    def send_units_to_game(self, translated_oob):
        force = translated_oob['force']
        logger.info(f'Populating {force} units into game engine.')
        # TODO: switch the the appropriate side and force based on the translated_oob['force']
        # For the current poc, we will assume the user has already navigated to the correct screen

        # TODO: need to pre-calculate and cache the screen location of all units so
        # that the find function doesn't get confused when there are units with the
        # same name present in the "Chosen" section. Or something. Maybe we could
        # drop everything with an x-left greater than a certain value, based on the
        # location of the x-left of the word "Chosen". There's definitely a bug in
        # the current lazy implementation, because you could have a unit type, like
        # a platoon, appear on the right before it's clicked, if you say added a
        # company containing that platoon first.
        current_class_page = 'infantry'
        unit_button_locations = {}
        for unit in translated_oob['units']:
            # Navigate to appropriate page for unit class
            target_class = unit['class']
            if target_class != current_class_page:
                click_target_text(target_class)
                current_class_page = target_class

            # Get target unit button coordinates from cache, otherwise find from screen
            try:
                target_x, target_y = unit_button_locations[unit['name']]
            except KeyError:
                target_x, target_y = find_target_text(unit['name'])
                unit_button_locations[unit['name']] = (target_x, target_y)

            click_at_location(target_x, target_y)

        # click the "OK" button to navigate away from the unit selection screen.
        logger.info(f'Population of {force} units complete. Navigating back to main scenario screen.')
        click_target_text('OK')


    def capture_screen(self):
        # Capture the entire screen and return the screenshot image.
        screenshot = pyautogui.screenshot()

        screenshot_path = SCREENSHOTS_DIR / f'{str(int(datetime.now().timestamp()))}.png'
        logger.debug(f'Saving screenshot to {screenshot_path}')
        screenshot.save(screenshot_path)

        return screenshot, screenshot_path


    def get_bbox_for_text(self, target_text, image):
        logger.debug(f'Attempting to find the text "{target_text}" in image.')
        # TODO: share this between function calls
        # Initialize the EasyOCR reader
        reader = easyocr.Reader(['en'])
        # Perform text detection on the image
        result = reader.readtext(image)

        # Search for the target_text in the detected text
        target_bbox = None
        # phrases will be populated with all the strings found on the page. If the
        # first pass doesn't find an exact match, then we'll use this phrases list
        # to find the best phrase that was probably OCR'd wrong.
        phrases = []
        all_results = []
        for detection in result:
            all_results.append(detection)
            detected_text, bbox = detection[1], detection[0]
            phrases.append(detected_text)
            if target_text in detected_text:
                target_bbox = bbox
                logger.debug(f'Found target text "{target_text}" in the image at bbox {target_bbox}.')
                break

        # if there isn't an exact match, try to find the best match that you can
        if target_bbox is None:
            logger.debug(f'Unable to find exact text "{target_text}". Searching for best match.')
            logger.debug(f'available phrases: {phrases}')
            best_match_text = fuzz_process.extractOne(target_text, phrases, scorer=fuzz.ratio)[0]
            logger.debug(
                f'Unable to find perfect match for "{target_text}". Using best match "{best_match_text}" instead.'
            )
            best_match_index = phrases.index(best_match_text)
            best_match_detection = result[best_match_index]
            logger.debug(f'Full bbox info for best match: {best_match_detection}')
            target_bbox = best_match_detection[0]

        return target_bbox

    def _find_center_of_bounding_box(self, bbox):
        # bbox should be a list of four points in the format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        # We'll assume that bbox is always in the correct format with four points.

        # Calculate the average x-coordinate and y-coordinate
        center_x = sum(point[0] for point in bbox) // 4
        center_y = sum(point[1] for point in bbox) // 4

        return (center_x, center_y)

    # TODO: note to self: might make sense to pre-calcualte and cache all the text locations.
    def find_target_text(self, target_text):
        screenshot, screenshot_path = self.capture_screen()

        # TODO: would be nice to use the screenshot, instead of reading the image
        # from disk here. Was having trouble, moved on.
        target_bbox = self.get_bbox_for_text(target_text, str(screenshot_path))
        target_x, target_y = self._find_center_of_bounding_box(target_bbox)

        return (target_x, target_y)

    def click_at_location(self, target_x, target_y):
        pyautogui.moveTo(target_x, target_y)
        pyautogui.click()

    def click_target_text(self, target_text):
        target_x, target_y = self.find_target_text(target_text)
        self.click_at_location(target_x, target_y)


class Screen(Enum):
    SCENARIO_EDITOR = 1
    UNIT_EDITOR = 2

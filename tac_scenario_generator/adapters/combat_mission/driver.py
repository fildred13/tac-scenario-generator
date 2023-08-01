import logging
from datetime import datetime
from enum import Enum

# TODO: if we stick with easyOCR, we should archive the model weights with this
# project so that it's reproducible even if EasyOCR changes in the future.
import easyocr
import pyautogui
from thefuzz import fuzz
from thefuzz import process as fuzz_process

from tac_scenario_generator.adapters.combat_mission.errors import \
    ScreenStateError
from tac_scenario_generator.settings import SCREENSHOTS_DIR

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

    def populate_oob(self, oob):
        """Given an OOB as prepared by the adapter's generate_oob(), populate the units for
        the oob into the editor. Presumes that the screen is already navigated
        to the main scenario editor screen.
        """
        logger.info(f'Populating {oob["army"]} OOB')
        self._go_to_unit_editor()

        # Select correct army
        if oob['army'] == 'Allied':
            self.click_text('Axis')
        elif oob['army'] == 'Axis':
            pass
        else:
            raise ValueError(f'Army must be either "Allied" or "Axis". Got {oob["army"]}.')

        for nation, waves in oob['nations'].items():
            nation_label_text = 'FORCE' if self._game_id == 'cmbo' else 'Nation'
            self._click_below_label(nation_label_text)
            self.click_text(nation)

            for wave, unit_types in waves.items():
                wave_label_text = 'LOCATION' if self._game_id == 'cmbo' else 'Location'
                self._click_below_label(wave_label_text)
                self.click_text(wave)

                for unit_type, units in unit_types.items():
                    if unit_type == 'Artillery' or unit_type == 'Air':
                        unit_type_label_text = 'Artillery' if self._game_id == 'cmbo' else 'Artillery/Air'
                    else:
                        unit_type_label_text = unit_type
                    self.click_text(unit_type_label_text)

                    for unit in units:
                        self.click_text(unit['name'])

        self._go_to_scenario_editor()
        logger.info(f'Finished populating {oob["army"]} OOB')

    def _click_below_label(self, label_text):
        x, y, bbox = self.find_text(label_text)
        self.click_at_location(x, y + self._get_bbox_height(bbox))

    def _go_to_unit_editor(self):
        if self._current_screen is not Screen.SCENARIO_EDITOR:
            raise ScreenStateError(
                'Driver does not yet support navigating to Unit Editor screen except '
                'from Scenario Editor screen. Current screen is {current_screen.name}.'
            )
        if self._game_id == 'cmbo':
            text = 'UNITS'
        else:
            text = 'UNIT'  # EasyOCR doesn't merge "UNIT EDITOR", so we just target the top, unique word.
        self.click_text(text)
        self._current_screen = Screen.UNIT_EDITOR

    def _go_to_scenario_editor(self):
        if self._current_screen is not Screen.UNIT_EDITOR:
            raise ScreenStateError(
                'Driver does not yet support navigating to Scenario Editor screen except '
                'from Unit Editor screen. Current screen is {current_screen.name}.'
            )
        self.click_text('OK')
        self._current_screen = Screen.SCENARIO_EDITOR

    # TODO: reconsider all of the below functions, and get them above this line or delete them

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

    def _get_bbox_height(self, bbox):
        return max(point[1] for point in bbox) - min(point[1] for point in bbox)

    # TODO: note to self: might make sense to pre-calcualte and cache all the text locations.
    def find_text(self, text):
        screenshot, screenshot_path = self.capture_screen()

        # TODO: would be nice to use the screenshot, instead of reading the image
        # from disk here. Was having trouble, moved on.
        bbox = self.get_bbox_for_text(text, str(screenshot_path))
        x, y = self._find_center_of_bounding_box(bbox)

        return (x, y, bbox)

    def click_at_location(self, target_x, target_y):
        pyautogui.moveTo(target_x, target_y)
        pyautogui.click()

    def click_text(self, target_text):
        target_x, target_y, _ = self.find_text(target_text)
        self.click_at_location(target_x, target_y)


class Screen(Enum):
    SCENARIO_EDITOR = 1
    UNIT_EDITOR = 2

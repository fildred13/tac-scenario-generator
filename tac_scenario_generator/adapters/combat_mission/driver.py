import logging
import time
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

        # These will be lazily populated as needed
        self._reader = None
        self._chosen_label_bbox = None
        self._fortification_label_bbox = None

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
            self.click_text('Allied')
        elif oob['army'] == 'Axis':
            pass
        else:
            raise ValueError(f'Army must be either "Allied" or "Axis". Got {oob["army"]}.')

        for nation, waves in oob['nations'].items():
            nation_label_text = 'FORCE' if self._game_id == 'cmbo' else 'Nation'
            self._click_below_label(nation_label_text)
            self.click_text(nation)

            for wave, divisions in waves.items():
                wave_label_text = 'LOCATION' if self._game_id == 'cmbo' else 'Location'
                self._click_below_label(wave_label_text)
                self._click_wave_selection(wave)

                for division, unit_types in divisions.items():
                    if self._game_id != 'cmbo':
                        self._click_below_label('Division')
                        self.click_text(division)

                    for unit_type, units in unit_types.items():
                        if unit_type == 'Artillery' or unit_type == 'Air':
                            unit_type_label_text = 'Artillery' if self._game_id == 'cmbo' else 'Artillery/Air'
                        else:
                            unit_type_label_text = unit_type
                        self.click_unit_type(unit_type_label_text)

                        for unit in units:
                            self.add_unit(unit['name'])

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
            text = 'Unit'  # EasyOCR doesn't merge "UNIT EDITOR", so we just target the top, unique word.
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
        screenshot.save(screenshot_path)

        return screenshot, screenshot_path

    def get_bbox_for_text(self, target_text, image, best_match=True, max_matches=10):
        """Gets the bbox for a given target_text in the given image. Uses fuzzy
        matching if an exact match cannot be found. If best_match is True
        (default) then only a single, best-guess bbox for the best matching
        piece of text will be returned, no matter how unconfident this function
        is.

        If best_match=False, then this function will return a list of the top
        max_matches best matches, where the list is sorted by fuzz_ratio (int of how
        similar the text is to the target text, between 0 and 100), and is of the
        shape:
            [{'text': <text>:, 'bbox': <bbox>, 'fuzz_ratio': <fuzz_ratio>}]
        """
        logger.debug(f'Attempting to find the text "{target_text}" in image.')
        if not self._reader:
            self._reader = easyocr.Reader(['en'])

        # Perform text detection on the image, storing all found pieces of text.
        boxcars = self._reader.readtext(image)

        # phrases will be populated with all the strings found on the page.
        phrases = []
        results = []
        for detection in boxcars:
            detected_text = detection[1]
            bbox = detection[0]
            phrases.append(detected_text)
            if target_text in detected_text:
                prepared_result = {'text': detected_text, 'bbox': bbox, 'fuzz_ratio': 100}
                results.append(prepared_result)
                if best_match:
                    # We assume if we've found an exact match that it's the correct
                    # instance of the phrase. This can be wrong if the actual
                    # target isn't actually the first occurrence of the word on the
                    # page, so we have to be careful about using the
                    # best_match: True option.
                    break

        logger.debug(f'Available phrases: {phrases}')
        # if there isn't an exact match or if we are trying to find all
        # possible matches, then try to find the best match that we can using
        # fuzzy matching
        if not best_match or results == []:
            best_match_texts = fuzz_process.extract(target_text, phrases, scorer=fuzz.ratio)
            for text in best_match_texts:
                match_index = phrases.index(text[0])
                detection = boxcars[match_index]
                results.append({'text': detection[1], 'bbox': detection[0], 'fuzz_ratio': text[1]})
                if 0 < max_matches <= len(results):
                    break

        prepared_results = sorted(results, key=lambda d: d['fuzz_ratio'], reverse=True)
        logger.debug(prepared_results)
        if best_match:
            return prepared_results[0]['bbox']
        elif max_matches > 0:
            return prepared_results[:max_matches]
        else:
            return prepared_results

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
        pyautogui.moveTo(0, 0)

    def click_text(self, target_text):
        target_x, target_y, _ = self.find_text(target_text)
        self.click_at_location(target_x, target_y)
        # let the UI catch up to the click
        time.sleep(0.2)

    def click_unit_type(self, unit_type):
        """In the unit editor, click the indicated unit type so that you're viewing units of that type."""
        # This handles the special case of the 'infantry' unit type, which can
        # fail to be clicked on when the 'infantry' division is also selected.
        if unit_type in ['Infantry'] and self._game_id in ['cmak', 'cmbb']:
            screenshot, screenshot_path = self.capture_screen()
            matches = self.get_bbox_for_text(unit_type, str(screenshot_path), best_match=False, max_matches=0)
            if not self._fortification_label_bbox:
                self._fortification_label_bbox = self.get_bbox_for_text('Fortification', str(screenshot_path))
            fort_top_x = self._fortification_label_bbox[0][1]
            best_matches = []
            for m in matches:
                match_top_x = m['bbox'][0][1]
                if match_top_x > fort_top_x - 10 and match_top_x < fort_top_x + 10:
                    best_matches.append(m)
            best_match = sorted(best_matches, key=lambda d: d['fuzz_ratio'], reverse=True)[0]
            x, y = self._find_center_of_bounding_box(best_match['bbox'])
            self.click_at_location(x, y)
            time.sleep(0.2)
        else:
            self.click_text(unit_type)

    def add_unit(self, unit_name):
        # TODO: this function, as well as click_unit_type, above, would benefit
        # from a refactor where we rethink what options we offer for "click
        # text" so we can pass constraints like "must be to the left of this
        # other text", "must be on the same line as this other text", etc. The
        # way it's structured right now doesn't lend itself to that. hence,
        # these custom functions.

        # The reason we need this special function is so we don't accidentally
        # click units that are in the "chosen" area.
        screenshot, screenshot_path = self.capture_screen()
        matches = self.get_bbox_for_text(unit_name, str(screenshot_path), best_match=False, max_matches=0)
        if not self._chosen_label_bbox:
            self._chosen_label_bbox = self.get_bbox_for_text('CHOSEN', str(screenshot_path))
        best_match = None
        for m in matches:
            try:
                best_match_fuzz_ratio = best_match['fuzz_ratio']
            except TypeError:
                best_match_fuzz_ratio = 0
            if m['bbox'][0][0] < self._chosen_label_bbox[0][0] and m['fuzz_ratio'] > best_match_fuzz_ratio:
                best_match = m
        x, y = self._find_center_of_bounding_box(best_match['bbox'])
        self.click_at_location(x, y)
        logger.debug(f"Added unit {unit_name} by clicking the text {best_match['text']}")
        time.sleep(0.2)

    def _click_wave_selection(self, wave_text):
        """Because the OCR is sketchy for picking the correct wave, this
        function instead finds the words "on map", which is reliable, and then
        moves down a certain number of rows. It's experimental, but seems to be
        much more reliable than pure OCR. Assumes that the "wave selection" box
        is already displayed on screen.
        """
        if wave_text == "On Map":
            self.click_text(wave_text)
            return

        x, y, bbox = self.find_text("On Map")
        logger.debug('##########')
        logger.debug(wave_text)
        reinforce_wave_int = int(wave_text.split(' ')[1])
        logger.debug(reinforce_wave_int)
        offset = self._get_bbox_height(bbox) * reinforce_wave_int
        self.click_at_location(x, y + offset)


class Screen(Enum):
    SCENARIO_EDITOR = 1
    UNIT_EDITOR = 2

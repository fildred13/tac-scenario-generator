import json
import logging
import os
import time
from datetime import datetime

# TODO: if we stick with easyOCR, we should archive the model weights with this
# project so that it's reproducible even if EasyOCR changes in the future.
import easyocr
import pyautogui
from thefuzz import process as fuzz_process

from settings import SCREENSHOTS_DIR


logger = logging.getLogger(__name__)


def send_units_to_game(translated_oob):
    logger.info('Populating {force} units into game engine.')
    # TODO: switch the the appropriate side and force based on the translated_oob['force']

    # TODO: need to pre-calculate and cache the screen location of all units so
    # that the find function doesn't get confused when there are units with the
    # same name present in the "Chosen" section. Or something. Maybe we could
    # drop everything with an x-left greater than a certain value, based on the
    # location of the x-left of the word "Chosen".

    for unit in translated_oob['units']:
        # TODO: in the translated_oob, need to group units by their type so that we can switch unit types. Right now we only support infantry.
        find_and_click_target_text(unit['type'])

    # click the "OK" button to navigate away from the unit selection screen.
    logger.info('Population of {force} units complete. Navigating back to main scenario screen.')
    find_and_click_target_text('OK')



def capture_screen():
    # Capture the entire screen and return the screenshot image.
    screenshot = pyautogui.screenshot()

    screenshot_path = SCREENSHOTS_DIR / f'{str(int(datetime.now().timestamp()))}.png'
    logger.debug(f'Saving screenshot to {screenshot_path}')
    screenshot.save(screenshot_path)

    return screenshot, screenshot_path


def get_bbox_for_text(target_text, image):
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
        best_match_text = fuzz_process.extractOne(target_text, phrases)[0]
        logger.debug(f'Unable to find perfect match for "{target_text}". Using best match "{best_match_text}" instead.')
        best_match_index = phrases.index(best_match_text)
        best_match_detection = result[best_match_index]
        logger.debug(f'Full bbox info for best match: {best_match_detection}')
        target_bbox = best_match_detection[0]

    return target_bbox


def find_center_of_bounding_box(bbox):
    # bbox should be a list of four points in the format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    # We'll assume that bbox is always in the correct format with four points.

    # Calculate the average x-coordinate and y-coordinate
    center_x = sum(point[0] for point in bbox) // 4
    center_y = sum(point[1] for point in bbox) // 4

    return center_x, center_y


# TODO: note to self: might make sense for CM to pre-calcualte and cache all the text locations.
def find_and_click_target_text(target_text):
    # The script currently assumes that the user will navigate to the game
    # window after initializing the script, to simplify development. We'll want
    # to replace this with something which automatically maximizes the game in
    # the future. This sleep provides the user time to do that.
    print('Script starting. Please navigate to the game now, and wait at least 3 seconds before navigating away.')
    time.sleep(3)

    screenshot, screenshot_path = capture_screen()

    # TODO: would be nice to use the screenshot, instead of reading the image from disk here. Was having trouble, moved on.
    target_bbox = get_bbox_for_text(target_text, str(screenshot_path))
    target_x, target_y = find_center_of_bounding_box(target_bbox)
    print(f'center of text {target_text} is {target_x}, {target_y}')

    # Send a mouse click on the target text's position
    pyautogui.moveTo(target_x, target_y)

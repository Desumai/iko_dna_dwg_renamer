# Import required packages
import cv2
import numpy as np
import pytesseract
from PIL import Image

def reformat_dwg_num(dwgNum:str, excludeChars:list = [" ", "\n",".iam",".ipt","~"]) -> str:
    for chars in excludeChars:
        dwgNum = dwgNum.replace(chars, '')
    if(dwgNum[len(dwgNum) - 1] == "."):
        dwgNum = dwgNum[:len(dwgNum) - 1]
    return dwgNum

def reformat_sheet_num(sheetNum:str) -> tuple:
    parsedStr = sheetNum.upper().replace(" ","").replace('\t',"")
    try:
        if "OF" not in parsedStr:
            raise Exception()
        numList = parsedStr.split("OF")
        first = int(numList[0])
        second = int(numList[1])
        if(first > second) or first < 1 or second < 1:
            raise Exception()
        return (first, second)
    except Exception as e:
        raise Exception("Wrong Sheet Number format: '" + sheetNum.replace('\n','\\n') + "'")

        

def find_sheet_num_and_dwg_num_box_contour(boxContours: list, Y_TOLERANCE: int = 45) -> tuple:
    """
    Finds the contours for the sheet number box and drawing number box for a drawing page
    Returns tuple (sheet box contour, dwg num box contour)
    """
    lastRowY = -1
    for c in boxContours:
        x, y, w, h = cv2.boundingRect(c)

        if y > lastRowY:
            lastRowY = y
    lastX = -1
    for c in boxContours:
        x, y, w, h = cv2.boundingRect(c)
        if lastRowY - Y_TOLERANCE <= y <= lastRowY:
            if x > lastX:
                lastX = x
    secondLastX = -1
    for c in boxContours:
        x, y, w, h = cv2.boundingRect(c)
        if lastRowY - Y_TOLERANCE <= y <= lastRowY:
            if secondLastX < x < lastX:
                secondLastX = x
    sheetNumContour = None
    dwgNumContour = None
    for c in boxContours:
        x, y, w, h = cv2.boundingRect(c)
        if lastRowY - Y_TOLERANCE <= y <= lastRowY:
            if x == lastX:
                sheetNumContour = c
            elif x == secondLastX:
                dwgNumContour = c
    return (sheetNumContour, dwgNumContour)


def find_dwg_and_sheet_num(
    image: np.ndarray,
    output: list = [None, [None, None]],  # [dwg num, [sheet num, total sheets]]
    MIN_BOX_AREA: int = 3000,
    MIN_BOX_HEIGHT: int = 40,
    MAX_BOX_AREA_RATIO: float = 0.3464,
    DATA_BOX_HEADER_VERTICAL_SPLIT: float = 0.4,
    Y_TOLERANCE=45,
) -> None:
    """
    Finds the title and number of a drawing and stores the values in [output].
    [output] is a len(2) list of dwg #, dwg title. Values that could not be found
    will be None 
    Returns void

    @params:
        - image: ndarray representation of the drawing (np.ndarray)
        - output: stores the output results (list)
        - MIN_BOX_AREA: the minimum size of a drawing data box (int)
        - MIN_BOX_HEIGHT: minimum height for a contour to be potentially a drawing data box (int)
        - MAX_BOX_AREA_RATIO: the maximum size of a drawing data box, relative to the drawing size (float)
        - DRAWING_NUMBER_BOX_HEADER_HORIZONTAL_SPLIT: the height of the header text for the dwg # box, 
            as a decimal percentage of the height of the dwg # box (from the top) (float)
        - X_TOLERANCE: permissible x difference between two contours to be considered the same "column" (int)
        - Y_TOLERANCE: permissible y difference between two contours to be considered the same "row" (int)
        - MIN_TEXT_HEIGHT: minimum height for a contour to be potentially text (int)
        - MIN_TEXT_WIDTH: minimum width for a contour to be potentially text (int)
        - MIN_TEXT_AREA: minimum area for a contour to be potentially text (int)
        - MIN_PERCENT_INDENT: for dwg title box only. Minimum indent from the left edge if the box that a contour must have to
            potentially be dwg title text. A decimal percentage of the width of the dwg title box (float)
    """
    # get image dimensions
    imgHeight = image.shape[0]
    imgWidth = image.shape[1]
    imgArea = imgHeight * imgWidth

    ###### process image to get contours ######

    # Convert the image to gray scale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # apply binary threshold
    thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)[1]
    # invert image and apply otsu threshold
    threshInv = cv2.threshold(thresh, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[
        1
    ]
    # blur image
    blur = cv2.GaussianBlur(threshInv, (1, 1), 0)
    # re-invert the image
    reInv = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # find all contours
    contours, heiarchy = cv2.findContours(reInv, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # filter out countors too small or big to be info boxes
    dataBoxContours = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h < MIN_BOX_HEIGHT:
            continue
        if MIN_BOX_AREA < w * h < imgArea * MAX_BOX_AREA_RATIO:
            dataBoxContours.append(c)

    #find contours for sheet num and dwg num boxes
    sheetNumBoxContour, dwgNumBoxContour = find_sheet_num_and_dwg_num_box_contour(dataBoxContours, Y_TOLERANCE)

    ###### find drawing number ######

    # make sure dwg num field is found
    if dwgNumBoxContour is None:  # null check
        raise Exception("Drawing Number field not found")

    dwgX, dwgY, dwgW, dwgH = cv2.boundingRect(dwgNumBoxContour)
    # check if correct field was found
    headerText = pytesseract.image_to_string(
        image=image[
            dwgY : dwgY + round(DATA_BOX_HEADER_VERTICAL_SPLIT * dwgH),
            dwgX : dwgX + dwgW,
        ],
        config="--psm 6",
    )
    if "DRAWING#" not in headerText.upper():
        raise Exception(f"Wrong field found. Not a drawing number ('{headerText}' field found instead)")

    # read and save drawing number
    cropped = image[round(dwgY + DATA_BOX_HEADER_VERTICAL_SPLIT * dwgH) : dwgY + dwgH, dwgX : dwgX + dwgW]
    text = pytesseract.image_to_string(cropped, config="--psm 6")
    output[0] = reformat_dwg_num(text)

    ###### find sheet number ######
    
    #make sure sheet num field is found
    if sheetNumBoxContour is None: #null check
        raise Exception("Sheet Number field not found")
    sheetX, sheetY, sheetW, sheetH = cv2.boundingRect(sheetNumBoxContour)

    # check if correct field was found
    headerText = pytesseract.image_to_string(
        image=image[
            sheetY : sheetY + round(DATA_BOX_HEADER_VERTICAL_SPLIT * sheetH),
            sheetX : sheetX + sheetW,
        ], config="--psm 6"
    )
    if "SHEET" not in headerText.upper():
        raise Exception(f"Wrong field found. Not sheet number information  ('{headerText}' field found instead)")

    # read and save drawing number
    cropped = image[round(sheetY + DATA_BOX_HEADER_VERTICAL_SPLIT * sheetH) : sheetY + sheetH, sheetX : sheetX + sheetW]
    text = pytesseract.image_to_string(cropped, config="--psm 6")
    output[1] = reformat_sheet_num(text)
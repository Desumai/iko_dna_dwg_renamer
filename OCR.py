# Import required packages
import cv2
import numpy as np
import pytesseract
from PIL import Image

def reformat_dwg_num(dwgNum:str, excludeChars:list = [" ", "\n",".iam",".ipt","~"]):
    for chars in excludeChars:
        dwgNum = dwgNum.replace(chars, '')
    return dwgNum

def reformat_dwg_title(dwgTitle:str, excludeChars:list = ["\n"], replaceChars:dict = {" ":"_","@": '', '"': "in", "'": "ft", "&":"AND", "#":"NUM"}):
    for chars in excludeChars:
        dwgTitle = dwgTitle.replace(chars, '')
    for chars in replaceChars.keys():
        dwgTitle = dwgTitle.replace(chars, replaceChars[chars])
    #handle "/" characters
    while "/" in dwgTitle:
        index = dwgTitle.index("/")
        try:
            #is fraction
            if(dwgTitle[index - 1].isdigit() and dwgTitle[index + 1].isdigit()):
                #get numerator:
                numeratorIndex = index - 1
                for i in reversed(range(0,index)):
                    if(not dwgTitle[i].isdigit()):
                        break
                    numeratorIndex = i
                #get denominator
                denominatorIndex = index + 1
                for i in range(index + 1, len(dwgTitle)):
                    if(not dwgTitle[i].isdigit()):
                        break
                    denominatorIndex = i
                numVal = round(int(dwgTitle[numeratorIndex:index])/int(dwgTitle[(index + 1):(denominatorIndex + 1)]),4)
                dwgTitle = dwgTitle[:numeratorIndex] + str(numVal) + dwgTitle[denominatorIndex + 1:]
            #is "W/" ("with" abreviaton)
            elif(dwgTitle[index - 1].upper() == "W") and not dwgTitle[index - 2].isalnum():
                dwgTitle = dwgTitle[:index - 1] + "WITH" + dwgTitle[index + 1:]
            #is "C/W" ("comes with" abreviation)
            elif (dwgTitle[index - 1:index + 2].upper() == "C/W") and not dwgTitle[index - 2].isalnum() and not dwgTitle[index + 2].isalnum():
                dwgTitle = dwgTitle[:index - 1] + "WITH" + dwgTitle[index + 2:]
            else: #replace "/" with "-" 
                dwgTitle = dwgTitle[:index] + "-" + dwgTitle[index + 1:]
        except Exception as e:
            #replace "/" with "-" 
            dwgTitle = dwgTitle[:index] + "-" + dwgTitle[index + 1:]
    return dwgTitle

def find_dwg_num_box_contour(boxContours: list, Y_TOLERANCE: int = 45):
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
    contour = None
    for c in boxContours:
        x, y, w, h = cv2.boundingRect(c)
        if x == secondLastX and lastRowY - Y_TOLERANCE <= y <= lastRowY:
            contour = c
    return contour


def find_dwg_title_box_contour(boxContours: list, X_TOLERANCE: int = 20):
    try:
        # get the x value of the right border edge of the drawing
        rightEdgeX = -1
        for c in boxContours:
            x, y, w, h = cv2.boundingRect(c)
            rightEdge = x + w
            if rightEdge > rightEdgeX:
                rightEdgeX = rightEdge

        # keep only right most boxes, remove others
        edgeContours = []
        for c in boxContours:
            x, y, w, h = cv2.boundingRect(c)
            if rightEdgeX - (x + w) <= X_TOLERANCE:
                edgeContours.append(c)

        # find title box, third last box
        edgeContours.sort(
            key=lambda c: cv2.boundingRect(c)[1], reverse=True
        )  # sort by descending y values
        return edgeContours[2]
    except Exception as e:
        return None


def find_dwg_num_and_title(
    image: np.ndarray,
    output: list = [None, None],  # [dwg num, dwg title]
    MIN_BOX_AREA: int = 3000,
    MIN_BOX_HEIGHT: int = 40,
    MAX_BOX_AREA_RATIO: float = 0.3464,
    DRAWING_NUMBER_BOX_HEADER_VERTICAL_SPLIT: float = 0.4,
    X_TOLERANCE: int = 20,
    Y_TOLERANCE=45,
    MIN_TEXT_HEIGHT: int = 10,
    MIN_TEXT_WIDTH: int = 10,
    MIN_TEXT_AREA: int = 500,
    MIN_PERCENT_INDENT: float = 0.1,
):
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
        if h < 30:
            continue
        if MIN_BOX_AREA < w * h < imgArea * MAX_BOX_AREA_RATIO:
            dataBoxContours.append(c)

    ###### find drawing number ######

    # find contours for dwg num field
    numBoxContours = find_dwg_num_box_contour(dataBoxContours, Y_TOLERANCE=Y_TOLERANCE)
    if numBoxContours is None:  # null check
        raise Exception("Drawing Number field not found")

    dwgX, dwgY, dwgW, dwgH = cv2.boundingRect(numBoxContours)
    # check if correct field was found
    headerText = pytesseract.image_to_string(
        image=image[
            dwgY : dwgY + round(DRAWING_NUMBER_BOX_HEADER_VERTICAL_SPLIT * dwgH),
            dwgX : dwgX + dwgW,
        ],
        config="--psm 6",
    )
    if "DRAWING#" not in headerText.upper():
        raise Exception(f"Wrong field found. Not a drawing number ('{headerText}')")

    # read and save drawing number
    cropped = image[round(dwgY + DRAWING_NUMBER_BOX_HEADER_VERTICAL_SPLIT * dwgH) : dwgY + dwgH, dwgX : dwgX + dwgW]
    text = pytesseract.image_to_string(cropped, config="--psm 6")
    output[0] = reformat_dwg_num(text)

    ###### find drawing title ######

    # find contours for dwg title field
    titleBoxContours = find_dwg_title_box_contour(dataBoxContours,X_TOLERANCE=X_TOLERANCE)
    if titleBoxContours is None:  # null check
        raise Exception("Drawing Title field not found")

    # crop dwg title field as its own image
    titleX, titleY, titleW, titleH = cv2.boundingRect(titleBoxContours)
    titleImg = image[titleY : titleY + titleH, titleX : titleX + titleW]

    # find text contours in dwg title field

    # Convert the image to gray scale
    titleGray = cv2.cvtColor(titleImg, cv2.COLOR_BGR2GRAY)

    # apply threshold
    titleThreshInv = cv2.threshold(
        titleGray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]
    rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    dialation = cv2.dilate(titleThreshInv, rectKernel, iterations=1)

    titleContoursList, _ = cv2.findContours(
        dialation, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
    )

    # find contours for title text inside dwg title box
    titleTextContours = []
    otherContours = []
    for i in range(len(titleContoursList)):
        x, y, w, h = cv2.boundingRect(titleContoursList[i])
        A = w * h
        if (
            A < MIN_TEXT_AREA
            or x < round(w * MIN_PERCENT_INDENT)
            or w < MIN_TEXT_WIDTH
            or h < MIN_TEXT_HEIGHT
        ):
            otherContours.append(
                np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
                .reshape((-1, 1, 2))
                .astype(np.int32)
            )
        else:
            titleTextContours.append(
                np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
                .reshape((-1, 1, 2))
                .astype(np.int32)
            )
    if len(titleTextContours) < 1:
        raise Exception("No drawing title found")
    
    #ensure field found is title box i.e. contains the text "TITLE"
    isTitleBox = False
    for c in otherContours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 30 or h < 10 or w * h < 300:
            continue
        tempImg = titleImg[y : y + h , x : x + w]
        text:str = pytesseract.image_to_string(tempImg, config="--psm 6")
        if("TITLE" in text.upper()):
            isTitleBox = True
            break
    if(not isTitleBox):
        raise Exception("Wrong field found. Not a drawing title")
    
    # read and save title text
    titleTextContours.sort(  # sort text by left to right, top down
        key=lambda c: cv2.boundingRect(c)[1] * 1000000 + cv2.boundingRect(c)[0],
        reverse=False,
    )
    titleComp = []
    for c in titleTextContours:
        x, y, w, h = cv2.boundingRect(c)
        textImg = titleImg[y : y + h, x : x + w]
        text = pytesseract.image_to_string(textImg, config="--psm 6")
        if text == "" or text == "\n" or text == " ":
            continue
        titleComp.append(text)
    if len(titleComp) < 1:
        raise Exception("No drawing title found")
    output[1] = reformat_dwg_title("-".join(titleComp))

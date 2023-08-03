# Import required packages
import cv2
import numpy as np
import pytesseract
from PIL import Image

def reformat_dwg_num(dwgNum:str, excludeChars:list = [" ", "\n",".iam",".ipt","~"]):
    for chars in excludeChars:
        dwgNum = dwgNum.replace(chars, '')
    return dwgNum

def reformat_dwg_title(dwgTitle:str, excludeChars:list = ["\n"], replaceChars:dict = {" ":"_","@": '', '"': "in", "'": "ft"}):
    for chars in excludeChars:
        dwgTitle = dwgTitle.replace(chars, '')
    for chars in replaceChars.keys():
        dwgTitle = dwgTitle.replace(chars, replaceChars[chars])
    #convery fractions to decimals
    while "/" in dwgTitle:
        index = dwgTitle.index("/")
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
    return dwgTitle

def opencv_find_dwg_num(
    image: Image, MIN_BOX_AREA: int = 3000, MAX_AREA_RATIO: float = 0.3464, Y_TOLERANCE=50, MIN_BOX_HEIGHT:int = 40
):

    # image data
    imgHeight = image.shape[0]
    imgWidth = image.shape[1]
    imgArea = imgHeight * imgWidth

    # Preprocessing the image starts
    # Convert the image to gray scale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # invert image and apply threshold
    threshInv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # blur image then dialate
    blur = cv2.GaussianBlur(threshInv, (1, 1), 0)
    dilalate = cv2.dilate(blur, np.ones((3, 3)))

    # re-invert the image
    reInv = cv2.threshold(dilalate, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # find all contours
    contours, heiarchy = cv2.findContours(reInv, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # filter contours to get info boxes
    # find the dwg# box
    filteredContours = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if(h < MIN_BOX_HEIGHT):
            continue
        if MIN_BOX_AREA < w * h < imgArea * MAX_AREA_RATIO:
            filteredContours.append(c)

    lastRowY = -1
    for c in filteredContours:
        x, y, w, h = cv2.boundingRect(c)

        if y > lastRowY:
            lastRowY = y
    lastX = -1
    for c in filteredContours:
        x, y, w, h = cv2.boundingRect(c)
        if lastRowY - Y_TOLERANCE <= y <= lastRowY:
            if x > lastX:
                lastX = x
    secondLastX = -1
    for c in filteredContours:
        x, y, w, h = cv2.boundingRect(c)
        if lastRowY - Y_TOLERANCE <= y <= lastRowY:
            if secondLastX < x < lastX:
                secondLastX = x
    contour = None
    for c in filteredContours:
        x, y, w, h = cv2.boundingRect(c)
        if x == secondLastX and lastRowY - Y_TOLERANCE <= y <= lastRowY:
            contour = c

    if contour is None:
        """
        cv2.drawContours(image, filteredContours, -1, (0,255,0),1,cv2.LINE_AA)
        cv2.namedWindow("window", cv2.WINDOW_GUI_NORMAL)
        cv2.imshow("window", image)
        cv2.waitKey(0)
        """
        raise Exception("Drawing Number field not found")
    dwgX, dwgY, dwgW, dwgH = cv2.boundingRect(contour)

    # check if correct field was found
    headerText = pytesseract.image_to_string(
        image=image[dwgY : dwgY + round(0.4 * dwgH), dwgX : dwgX + dwgW], config="--psm 6"
    )
    if "DRAWING#" not in headerText:
        """
        cv2.drawContours(image, filteredContours, -1, (0,255,0),1,cv2.LINE_AA)
        imgCopy = cv2.resize(image,(1920-16*10, 1080-9*10))
        cv2.imshow("window", imgCopy)
        cv2.waitKey(0)
        #cv2.imshow("img", image[dwgY : dwgY + dwgH, dwgX : dwgX + dwgW])
        """
        raise Exception(f"Wrong field found ('{headerText}')")

    # read and return drawing number
    cropped = image[round(dwgY + 0.4 * dwgH) : dwgY + dwgH, dwgX : dwgX + dwgW]

    return reformat_dwg_num(
        pytesseract.image_to_string(image=cropped, config="--psm 6")
    )

def opencv_find_dwg_title(
    image: Image,
    MIN_BOX_AREA:int = 3000,
    MAX_BOX_AREA_RATIO: float = 0.3464,
    X_TOLERANCE:int=20,
    MIN_TEXT_AREA:int = 500,
    MIN_TEXT_HEIGHT:int = 10,
    MIN_TEXT_WIDTH:int = 10,
    MIN_PERCENT_INDENT:float = 0.1
):
    imgHeight = image.shape[0]
    imgWidth = image.shape[1]
    imgArea = imgHeight * imgWidth

    # Preprocessing the image starts

    # Convert the image to gray scale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)[1]
    # invert image and apply threshold
    threshInv = cv2.threshold(thresh, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[
        1
    ]

    # blur image then dialate
    blur = cv2.GaussianBlur(threshInv, (1, 1), 0)

    # re-invert the image
    reInv = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # find all contours
    contours, heiarchy = cv2.findContours(reInv, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # find title box

    # filter out countors too small or big to be info boxes
    filteredContours = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h < 30:
            continue
        if MIN_BOX_AREA < w * h < imgArea * MAX_BOX_AREA_RATIO:
            filteredContours.append(c)

    # get the x value of the right border edge of the drawing
    rightEdgeX = -1
    for c in filteredContours:
        x, y, w, h = cv2.boundingRect(c)
        rightEdge = x + w
        if rightEdge > rightEdgeX:
            rightEdgeX = rightEdge

    # keep only right most boxes, remove others
    edgeContours = []
    for c in filteredContours:
        x, y, w, h = cv2.boundingRect(c)
        if rightEdgeX - (x + w) <= X_TOLERANCE:
            edgeContours.append(c)

    # find title box, third last box
    edgeContours.sort(
        key=lambda c: cv2.boundingRect(c)[1], reverse=True
    )  # sort by descending y values
    titleContour = edgeContours[2]

    titleX, titleY, titleW, titleH = cv2.boundingRect(titleContour)
    titleImg = image[titleY : titleY + titleH, titleX : titleX + titleW]
    # Convert the image to gray scale
    titleGray = cv2.cvtColor(titleImg, cv2.COLOR_BGR2GRAY)

    # apply threshold
    titleThreshInv = cv2.threshold(
        titleGray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]
    rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    dialation = cv2.dilate(titleThreshInv, rectKernel, iterations=1)
    titleReInv = cv2.threshold(
        titleThreshInv, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]
    
    titleContours, _ = cv2.findContours(dialation, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    boxContours = []
    otherBoxContours = []
    for i in range(len(titleContours)):
        x, y, w, h = cv2.boundingRect(titleContours[i])
        A = w * h
        if A < MIN_TEXT_AREA or x < round(w * MIN_PERCENT_INDENT) or w < MIN_TEXT_WIDTH or h < MIN_TEXT_HEIGHT:
            otherBoxContours.append(
                np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
                .reshape((-1, 1, 2))
                .astype(np.int32)
            )
        else:
            boxContours.append(
                np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
                .reshape((-1, 1, 2))
                .astype(np.int32)
            )
    # check if is title box
    isTitleBox = False
    for c in otherBoxContours:
        x, y, w, h = cv2.boundingRect(c)
        if w < MIN_TEXT_WIDTH or h < MIN_TEXT_HEIGHT:
            continue
        textImg = titleImg[y : y + h, x : x + w]
        text = pytesseract.image_to_string(textImg, config="--psm 6")
        if "TITLE" in text.upper():
            isTitleBox = True
            break
    if not isTitleBox:
        raise Exception("Title box not found")

    # read title text
    boxContours.sort(  # sort text by left to right, top down
        key=lambda c: cv2.boundingRect(c)[1] * 1000000 + cv2.boundingRect(c)[0],
        reverse=False,
    )
    titleComp = []
    for c in boxContours:
        x, y, w, h = cv2.boundingRect(c)
        textImg = titleImg[y : y + h, x : x + w]
        text = (
            pytesseract.image_to_string(textImg, config="--psm 6")
        )
        if text == "" or text == "\n":
            continue
        titleComp.append(text)
    return reformat_dwg_title("-".join(titleComp))
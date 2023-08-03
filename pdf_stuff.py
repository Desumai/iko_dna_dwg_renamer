import fitz, sys
from fitz import Pixmap
import numpy as np
from PIL import Image
from cv2 import imdecode

# Print iterations progress. from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
def printProgressBar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    printEnd="\r",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    sys.stdout.write(f"\r{prefix} |{bar}| {percent}% {suffix}")
    sys.stdout.write(printEnd)
    sys.stdout.flush()
    # Print New Line on Complete
    if iteration == total:
        print()

def pdf_to_np_array_list(filePath:str):
    imgList = []
    with fitz.open(filePath) as file:
        numOfPages = len(file)
        print(f"{numOfPages} drawings found.")
        print("Converting PDF to images...")
        printProgressBar(0, numOfPages,prefix="Progress: ", suffix="({:<15}".format(f"{0}/{numOfPages})"))
        for i, page in enumerate(file):
            pixmap:Pixmap = page.get_pixmap(dpi =300)
            npArr = imdecode(np.frombuffer(pixmap.tobytes(), dtype=np.uint8), -1)
            imgList.append(npArr)
            printProgressBar(i + 1, numOfPages,prefix="Progress: ", suffix="({:<15}".format(f"{i + 1}/{numOfPages})"))
    #printProgressBar(numOfPages, numOfPages,prefix="Progress: ", suffix="({:<15}".format(f"{numOfPages}/{numOfPages})"))
    print("\n")
    return imgList


import fitz
from fitz import Pixmap
import numpy as np
from PIL import Image
from cv2 import imdecode


def pdf_to_np_array_list(filePath:str):
    imgList = []
    with fitz.open(filePath) as file:
        for i, page in enumerate(file):
            pixmap:Pixmap = page.get_pixmap(dpi =300)
            npArr = imdecode(np.frombuffer(pixmap.tobytes(), dtype=np.uint8), -1)
            imgList.append(npArr)
    return imgList

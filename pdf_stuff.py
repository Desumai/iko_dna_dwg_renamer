import pdf2image, fitz
from fitz import Pixmap
import numpy as np
from PIL import Image
from cv2 import imdecode

def convert_pdf_to_image_list(filePath: str,popplerPath:str):
    return pdf2image.convert_from_path(
        filePath, poppler_path=popplerPath, fmt="png", dpi=300, thread_count=10
    )

def pdf_to_np_array_list(filePath:str):
    imgList = []
    with fitz.open(filePath) as file:
        for i, page in enumerate(file):
            pixmap:Pixmap = page.get_pixmap(dpi =300)
            npArr = imdecode(np.frombuffer(pixmap.tobytes(), dtype=np.uint8), -1)
            imgList.append(npArr)
    return imgList

def save_temp_imgs(images:list, tempPath:str):
    imgDict = {}
    for i, image in enumerate(images):
        path = tempPath + "\\" + "{:03d}".format(i) + ".png"
        image.save(path, "png")
        imgDict[i] = path
    return imgDict

def save_temp_imgs_from_pdf(images:list, filePath: str, popplerPath: str, tempPath:str = "temp"):
    imageList = convert_pdf_to_image_list(filePath=filePath,popplerPath=popplerPath)
    save_temp_imgs(images=imageList)
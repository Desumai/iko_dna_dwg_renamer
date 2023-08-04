import fitz
from fitz import Pixmap, Page, Document
import numpy as np
from cv2 import imdecode

def pdf_page_to_np_array(page:Page):
    pixmap:Pixmap = page.get_pixmap(dpi =300)
    return imdecode(np.frombuffer(pixmap.tobytes(), dtype=np.uint8), -1)

def save_page_as_pdf(fileName:str, originalPdf:Document, pageNum:int):
    saveFile:Document = fitz.open()
    saveFile.insert_pdf(originalPdf, pageNum, pageNum)
    saveFile.save(fileName)
    saveFile.close()
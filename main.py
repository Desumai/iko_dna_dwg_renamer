
from file_management import get_PDF_path, get_save_path
from pdf_stuff import pdf_page_to_np_array, save_page_as_pdf
from OCR import find_dwg_num_and_title
import os, consts, fitz
from pytesseract import pytesseract
import time



#set tesseract path
pytesseract.tesseract_cmd = consts.TESSERACT_PATH

print("Select input PDF package")
#get input file path
inputPath = get_PDF_path()
if(inputPath is None):
    raise Exception("No Input")

print("Select output directory")
#get save dir path
savePath = get_save_path()
if(savePath is None):
    raise Exception("No Input")

#create save folders
successPath = savePath + r"\complete"
failPath = savePath + r"\failed"
if not os.path.exists(successPath):
    os.makedirs(successPath)
if not os.path.exists(failPath):
    os.makedirs(failPath)

print("Processing Drawings...")
start = time.time()
with fitz.open(inputPath) as file:
    numOfPages = len(file)
    for i, page in enumerate(file):
        #process page into image numpy array for OCR
        image = pdf_page_to_np_array(page)
        #read drawing info
        result = [None,None] #dwg num, dwg title
        try:
            find_dwg_num_and_title(image,result)
            print("{:>4}".format(f"({i + 1}") +  f"/{numOfPages}): {result[0]}")
        except Exception as e:
            print("{:>4}".format(f"({i + 1}") +  f"/{numOfPages}): [ERROR] {e}")
        
        if(result[0] is not None and result[1] is not None):
            try:
                savePath = successPath + "\\" + result[1] + '-' + result[0] + ".pdf"
                save_page_as_pdf(savePath,file,i)
                continue
            except Exception as e:
                print("{:>4}".format(f"({i + 1}") +  f"/{numOfPages}): [ERROR] {e}")
        if (result[0] is not None):
            try:
                savePath = failPath + "\\" + result[0] + ".pdf"
                save_page_as_pdf(savePath, file, i)
                continue
            except Exception as e:
                print("{:>4}".format(f"({i + 1}") +  f"/{numOfPages}): [ERROR] {e}")
        savePath = failPath + "\\drawing" + "{:03d}".format(i) + ".pdf"
        save_page_as_pdf(savePath, file, i)
    pass

print(f"Done. Took {time.time() - start} seconds.")
input("Press ENTER to continue...")
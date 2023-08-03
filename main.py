
from file_management import get_PDF_path, get_save_path
from PyPDF2 import PdfReader,PdfWriter
from pdf_stuff import pdf_to_np_array_list
from OCR import find_dwg_num_and_title
import os, consts
from pytesseract import pytesseract




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

print("Parsing input PDF...")
pdfImages = pdf_to_np_array_list(inputPath)


print("Reading drawings...")

with open(inputPath, "rb") as file:
    inputPdf = PdfReader(file)
    numOfImages = len(pdfImages)
    for i, image in enumerate(pdfImages):
        result = [None,None] #dwg num, dwg title
        try:
            find_dwg_num_and_title(image,result)
            print("{:>4}".format(f"({i + 1}") +  f"/{numOfImages}): {result[0]}")
        except Exception as e:
            print("{:>4}".format(f"({i + 1}") +  f"/{numOfImages}): [ERROR] {e}")
        output = PdfWriter()
        output.add_page(inputPdf.pages[i])
        if(result[0] is not None and result[1] is not None):
            try:
                with open(successPath + "\\" + result[1] + '-' + result[0] + ".pdf", "wb") as outputStream:
                    output.write(outputStream)
                continue
            except Exception as e:
                print("{:>4}".format(f"({i + 1}") +  f"/{numOfImages}): [ERROR] {e}")
        if (result[0] is not None):
            try:
                with open(failPath + "\\" + result[0] + ".pdf", "wb") as outputStream:
                    output.write(outputStream)
                continue
            except Exception as e:
                print("{:>4}".format(f"({i + 1}") +  f"/{numOfImages}): [ERROR] {e}")
        with open(failPath + "\\drawing" + "{:03d}".format(i) + ".pdf", "wb") as outputStream:
            output.write(outputStream)
        continue
"""

print("Deleting temp files...")
for filename in os.listdir(consts.TEMP_PATH):
    file_path = os.path.join(consts.TEMP_PATH, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))
"""
print('done')
input("Press ENTER to continue...")
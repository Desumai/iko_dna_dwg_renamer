
from file_management import get_PDF_path, get_save_path
from pdf_stuff import pdf_page_to_np_array, save_page_as_pdf
from dwg_page import DwgPage
from OCR import find_dwg_and_sheet_num
from ui_stuff import printProgressBar
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
competed = 0
failed = 0
start = time.time()
with fitz.open(inputPath) as file:
    numOfPages = len(file)
    pageCache:list[DwgPage] = []
    for i, page in enumerate(file):
        #process page into image numpy array for OCR
        printProgressBar(i,numOfPages,prefix="Progress: ",suffix= f"({f'{i}/{numOfPages})':<10}", length= 50)
        image = pdf_page_to_np_array(page)
        #read drawing info
        result = [None,None] #[dwg num, (current sheet num, total sheet num)]
        try:
            find_dwg_and_sheet_num(image,result)
            print(end=consts.LINE_CLEAR)
            print("{:>4}".format(f"({i + 1}") +  f"/{numOfPages}): {result[0]:<60}")
        except Exception as e:
            print(end=consts.LINE_CLEAR)
            print("{:>4}".format(f"({i + 1}") +  f"/{numOfPages}): [ERROR] {e:<60}")
        
        newPage = DwgPage(pageNum = i, dwgNum = result[0], currentSheet = result[1][0], totalSheet = result[1][1])
        if(newPage.is_valid()):
            try:
                #check if page is not last in group
                if(not newPage.is_last_sheet()):
                    #check page cache (if not empty) if newPage is right after the last sheet
                    if(len(pageCache) > 0):
                        if newPage.is_right_after(pageCache[-1]):
                            pageCache.append(newPage)
                            continue
                        else:
                            raise Exception(f"Sheets for drawing '{newPage.dwgNum}' are not in order.")
                    pageCache.append(newPage)
                    continue
                else: #is last page in group
                    savePath = successPath + "\\" + newPage.dwgNum + ".pdf"
                    save_page_as_pdf(savePath,file,i,len(pageCache))
                    competed += 1 + len(pageCache)
                    pageCache = []
                    continue
            except Exception as e:
                print(end=consts.LINE_CLEAR)
                print("{:>4}".format(f"({i + 1}") +  f"/{numOfPages}): [ERROR] {e:<60}")
        pageCache.append(newPage)
        for page in pageCache:      
            savePath = failPath + "\\drawing" + "{:03d}".format(page.pageNum) + ".pdf"
            save_page_as_pdf(savePath, file, page.pageNum)
        failed += len(pageCache)
        pageCache = []
    printProgressBar(numOfPages,numOfPages,prefix="Progress: ",suffix= f"({f'{numOfPages}/{numOfPages})':<10}", length= 50)

print()
print(f"Done. {competed} pages successful, {failed} pages failed.")
print(f"Took {time.time() - start} seconds.")
input("Press ENTER to continue...")
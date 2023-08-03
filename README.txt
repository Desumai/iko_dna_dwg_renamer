Creator: siudust
Date: August 3, 2023
Version 0.1.1


Program Info:
Extracts and renames individual asset/item drawings from a DNA PDF drawing package.
Reads drawing number and title using Tesseract OCR and OpenCV.
Names drawings according to their drawing number and title (i.e. "{title}-{number}.pdf").
Successfully and unsuccessfully renamed items will be saved in the "completed" and "failed" folders, respectfully (in the selected output directory).

To Run:
To launch program, run "main.exe" located in the program folder.

About OpenCV:
OpenCV is an open source libary for computer vision.
Currently uses OpenCV v4.8.0 (python)
For more information on OpenCV, see https://docs.opencv.org/4.x/

About Tesseract OCR:
Tesseract is an open source libary for AI optical character recognition (OCR).
Currently uses Tesseract OCR v5.3.1
Can train the Tesseract build to get more accurate results.
Tesseract build is already installed in project directory (path = /tesseract).
Using Tesseract build from https://github.com/UB-Mannheim/tesseract/wiki
For more information on Tesseract OCR, see https://github.com/tesseract-ocr/tesseract

Notes:
Drawing names may be inaccurate. It is recommended to check over the files before uploading them to SharePoint,
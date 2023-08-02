import easygui

def get_PDF_path():
    """
    Opens a file picker dialog (easygui) for the user to select an input CSV file.
    Returns None if the user cancels the dialog.
    """
    importPATH = easygui.fileopenbox(
        msg="Please Select PDF File",
        title="Open File",
        default="c:\data\det\*.pdf",
        filetypes="*.pdf",
        multiple=False,
    )
    # ensure file is pdf
    if type(importPATH) == type(""):
        extIndex = importPATH.rindex(".")
        extStr = importPATH[extIndex + 1 :]
        if (extIndex <= 0) or (extStr.lower() != "pdf"):
            raise ValueError("File '" + importPATH + "' is not of type .pdf")

    return importPATH

def get_save_path(defaultSavePATH: str = None):
    """
    Opens a file picker dialog (easygui) for the user to select a directory to save
    the output images to. Returns None if the user cancels the dialog.
    @params
        defaultSavePATH - the file path to the default directory to save to. Optional. (str)

    """
    savePATH = easygui.diropenbox(title="Save To", default=defaultSavePATH)
    if savePATH is not None:
        savePATH = savePATH + "\\"
    return savePATH
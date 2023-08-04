
class DwgPage:
    def __init__(self, pageNum:int, dwgNum:str, currentSheet:int, totalSheet:int):
        self.pageNum = pageNum
        self.dwgNum = dwgNum
        self.currentSheet = currentSheet
        self.totalSheet = totalSheet
    
    def is_same_dwg(self, otherPage) -> bool:
        return (self.dwgNum == otherPage.dwgNum)
    
    def is_last_sheet(self) -> bool:
        return self.currentSheet == self.totalSheet
    
    def is_right_after(self, pageBefore) -> bool:
        return self.is_same_dwg(pageBefore) and (self.currentSheet - pageBefore.currentSheet == 1)
    
    def is_valid(self) -> bool:
        return (self.dwgNum is not None) and (self.currentSheet is not None) and (self.totalSheet is not None)
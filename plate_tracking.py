class plate:
    standard_wells = \
    ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12',
     'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12',
     'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12',
     'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12',
     'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12',
     'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
     'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12',
     'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12']

    def __init__(self, plateID, image_list):
        self.wells = self.standard_wells.copy()
        if plateID.startswith("WPS"):
            self.wells.remove("H1")
            self.wells.remove("H2")
        else:
            self.wells.remove("D7")
        self.plateID = plateID
        self.image_list = image_list
        self.mono_count, self.mono_ready_count = 0, 0
        self.poly_count, self.ambiguous_count = 0, 0
        self.empty_count = 0

    def get_wells(self):
        return self.wells

    def add_result(self, type, size=0):
        if type == "monoclonal":
            self.mono_count += 1
            if size > 1.5:
                self.mono_ready_count += 1
        elif type == "polyclonal":
            self.poly_count += 1
        elif type == "empty":
            self.empty_count += 1
        elif type == "ambiguous":
            self.ambiguous_count += 1

    def get_stats(self):
        stats = {"mono_count": self.mono_count,
               "mono_ready_count": self.mono_ready_count,
               "poly_count": self.poly_count,
               "empty_count": self.empty_count,
               "ambiguous_count": self.ambiguous_count}

        return stats
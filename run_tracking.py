from mq_utils import get_sorted_scans
from mq_utils import enumerateRunDir

class run:

    def __init__(self, run_path):
        self.plateIDs, self.image_list = enumerateRunDir(run_path)
        self.logstring, self.sumstring, self.statstring

    def is_d5_plus(self):
        """
        Verify scans are available to at least day 5
        (For at least one full plate)
        """
        d5p = False
        for p in self.plateIDs:
            if len(get_sorted_scans(self.imageList, p, "H12")) >= 5:
                d5p = True
        return d5p

    def get_plates(self):
        return self.plateIDs

    def get_image_list(self):
        return self.image_list
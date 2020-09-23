import mq_utils

class well:

    def __init__(self, image_list, plate_id, well_id):
        self.image_list = mq_utils.get_sorted_scans(image_list, plate_id, well_id)
        self.plate_id, self.well_id = plate_id, well_id
        self.fov = [0, 0, 0, 0]
        self.clonality = False  # Initialized as false, indicating not yet computed
        self.day_clons = {}
        self.poly_detections, self.negative_detections, self.positive_detections = 0, 0, 0
        self.object_fields = {}  # Day-by-day record of all detections' coords
        self.known_objects = []  # Object list
        self.current_class = ""

        self.run_id = self.image_list[0].split("/")[-1].split("_")[0]
        print("Processing " + self.run_id + " - " + plate_id + " - well " + well_id)

    def get_paths(self):
        """
        Returns paths for all images
        Specific to given run/plate/well
        Sorted and filtered by date
        """
        return self.image_list

    def is_identified(self):
        """
        Returns false if well is not declared identified
        """
        return self.clonality

    def add_result(self, img_results, day):
        """
        Writes results of process_image to well instance
        """
        self.day_clons[day] = img_results[0]
        self.fov = img_results[1]
        c = img_results[0]  # Classification
        if c == "empty":
            self.negative_detections += 1
            if day == len(self.image_list) - 1 or (self.negative_detections >= 3 and self.positive_detections <= 3):
                self.clonality = "empty"
        elif c == "poly":
            self.positive_detections += 1
            self.poly_detections += 1
            if self.poly_detections > 3:
                self.clonality = "poly"
            if day == 0:
                self.clonality = "poly"
        elif c == "diff":
            self.positive_detections += 1
            self.clonality = "diff"
        elif c == "mono":
            self.positive_detections += 1

        if day == 0:
            self.clonality = c
            if self.clonality == "empty" and len(self.known_objects) == 1:
                self.clonality = "monoclonal"
            elif self.clonality == "empty" and len(self.known_objects) > 1:
                self.clonality = "polyclonal"


        self.object_fields[day] = [img_results[3]]  # Store colony coords as day's object fields
        #self.add_known_object(img_results[3], day)

        known_count = 0
        for i in self.known_objects:
            if i["survived"] and i["biotic"]:
                known_count += 1
        print("\tNumber of known objects: " + str(known_count))

    def add_known_object(self, coord_list, day):  # Add coords for additional detection of known object
        if len(self.known_objects) == 0:
            for coords in coord_list:
                self.known_objects.append({day: coords, "biotic": True, "survived": True})
        elif len(coord_list) is not 0:
            for coords in coord_list:
                # Found matching colony, colony occurs within bounding box of future colony
                matched, within_later = False, False
                for i in self.known_objects:
                    if day + 1 in i:
                        latter_coords = i[day + 1]  # Coords of object from day after current
                        print("\tIdentity comparison " + str(coords) + " to " + str(latter_coords))
                        if mq_utils.is_within(coords, latter_coords):
                            print("\t\t" + str(coords) + " is within the later colony - " + str(latter_coords))
                            within_later = True
                        else:
                            print("\t\t" + str(coords) + " is NOT within the later colony - " + str(latter_coords))
                        if mq_utils.is_same_colony(coords, latter_coords, day):
                            print("\t\tColony at " + str(coords) + " matched with colony at " + str(latter_coords))
                            i[day] = coords
                            matched = True
                            break
                if not matched:
                    print("\tColony detection at " + str(coords) + " could not be matched.")
                    o = {day: coords, "biotic": True, "survived": True}
                    if not within_later:
                        o["survived"] = False
                        print("\tColony detection at " + str(coords) + " did not survive.")
                    self.known_objects.append(o)

    def check_biotics(self):
        """
        Iterates over known objects
        Flags objects as non-biotic if insufficient size change
        """
        for i in range(len(self.known_objects)):
            if self.known_objects[i]["survived"] and self.known_objects[i]["biotic"]:
                gi = self.calc_growth_index(self.known_objects[i])
                print("Growth index (colony " + str(i) + "): " + str(gi))
            if gi < 0.000000001:
                self.known_objects[i]["biotic"] = False

    def compute_d0_clonal(self):
        """
        Assess state of known objects after reverting to day 0 to infer clonality
        """
        col_count = 0
        for obj in self.known_objects:
            if obj["survived"] and obj["biotic"]:
                col_count += 1

        if col_count == 1:
            self.clonality = "mono"
        elif col_count > 1:
            self.clonality = "poly"
        elif col_count == 0:
            self.clonality = "ambiguous"



    def calc_growth_index(self, ko):
        """
        Calculates a parameter representing relative avg colony growth
        Sum of vertical and horizontal ratios
        """
        hrz_ratios, vrt_ratios = [], []
        hrz_vals, vrt_vals = [], []
        for day in ko:
            if isinstance(day, int) and (day + 1) in ko:
                hrz_vals.append(ko[day][2] - ko[day][0])
                vrt_vals.append(ko[day][3] - ko[day][1])
                hrz_diff = ((ko[day][2] - ko[day][0]) -
                            (ko[day + 1][2] - ko[day + 1][0]))
                vrt_diff = ((ko[day][3] - ko[day][1]) -
                            (ko[day + 1][3] - ko[day + 1][1]))
                hrz_ratio = hrz_diff / (ko[day + 1][2] - ko[day + 1][0])
                vrt_ratio = vrt_diff / (ko[day + 1][3] - ko[day + 1][1])
                hrz_ratios.append(hrz_ratio)
                vrt_ratios.append(vrt_ratio)
        if len(hrz_ratios) == 0:
            return 0
        avg_hrz = sum(hrz_ratios) / len(hrz_ratios)  # not currently returned by function
        avg_vrt = sum(vrt_ratios) / len(vrt_ratios)  # can change so function returns sum of avgs
        hrz_delta = (max(hrz_ratios) - min(hrz_ratios)) / len(hrz_ratios)
        vrt_delta = (max(vrt_ratios) - min(vrt_ratios)) / len(vrt_ratios)
        return avg_hrz + avg_vrt

    def get_class(self):
        return self.clonality

    def get_current_fov(self):
        return self.fov

    def output_class(self):
        if self.clonality == "poly":
            c = "polyclonal"
        elif self.clonality == "mono":
            c = "monoclonal"
        elif self.clonality == "diff":
            c = "Differentiated"
        else:
            c = "empty"
        print(self.run_id + " - " + self.plate_id + " - " + self.well_id + " is " + c + ".\n")
        return c

import os
import datetime
import shutil
import boto3
import requests as r

class output():

    def __init__(self, run, writefiles=False):
        self.write = writefiles  # Indicates whether files should in fact be written or ignored
        output_path = "Logs/"
        if self.write is True:
            if not os.path.isdir(output_path + run):
                os.mkdir(output_path + run)
            if not os.path.isdir("Details/" + run):
                os.mkdir("Details/" + run)
            self.summary = open(output_path + run + "/" + run + "_" +
                                datetime.datetime.now().strftime('%y-%m-%d-%H-%M') + "_summary.txt", "w")
            self.stats = open(output_path + run + "/" + run + "_" +
                                datetime.datetime.now().strftime('%y-%m-%d-%H-%M') + "_stats.txt", "w")
            self.picklist_path_dbx = output_path + run + "/" + run + "_" + datetime.datetime.now().strftime('%y-%m-%d-%H-%M') + "_picklist.txt"
            self.details_path = "Details/" + run + "/" + run + "_" + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".csv"
            self.details = open(self.details_path, "w")
            self.details.write("Plate,RowCol,Clonality,DateCaptured,PrimaryClassification,ConfidenceM1,ConfidenceM2," +
                                "ConfidenceM3,ConfidenceM4,DimX,DimY,CoordX1,CoordX2,CoordY1,CoordY2\n")


    def add_well(self, plateid, wellid, clonality, latest_date, classifier_results, coord_info, run_id):
        if self.write is False:
            return ""
        if clonality is "consolidated":
            print("\n" + plateid + "_" + wellid + " - SKIPPED - ALREADY CONSOLIDATED\n")
        else:  # Code to the right to exclude empties #elif clonality is not "empty":
            self.summary.write(run_id + "_" + plateid + " - " + wellid + " - " + clonality + "\n")
            if clonality == "monoclonal":
                classification, cm1, cm2, cm3, cm4 = classifier_results
            else:
                classification, cm1, cm2, cm3, cm4 = ["-", "-", "-", "-", "-"]
            self.details.write(run_id + "_" + plateid + "," + wellid + "," + clonality + "," + latest_date + "," + classification +
                               "," + str(cm1) + "," + str(cm2) + "," + str(cm3) + "," + str(cm4) + "," +
                               str(coord_info["dimx"]) + "," + str(coord_info["dimy"]) + "," +
                               str(coord_info["xmin"]) + "," + str(coord_info["ymin"]) + "," +
                               str(coord_info["xmax"]) + "," + str(coord_info["ymax"]) + "\n")


    def write_stats(self, stats, plateID):
        if self.write is False:
            return ""
        self.stats.write("[INFO]Report for " + plateID + ":\n")
        self.stats.write("Monoclonal wells ready for consolidation: " + str(stats["mono_ready_count"]) + "\n")
        self.stats.write("Monoclonal wells (total): " + str(stats["mono_count"]) + "\n")
        self.stats.write("Polyclonal wells:" + str(stats["poly_count"]) + "\n")
        self.stats.write("Ambiguous wells: " + str(stats["ambiguous_count"]) + "\n")
        self.stats.write("Empty wells: " + str(stats["empty_count"]) + "\n\n\n")


    def skip(self, plateID, reason_mode): ## REASON_MODE - a = activity, v = viewing
        if reason_mode == "a":
            reason = "PLATE NOT ACTIVE"
        elif reason_mode == "v":
            reason = "PLATE NOT FLAGGED FOR VIEWING"
        print("\n" + plateID + " - SKIPPED - " + reason + "\n")
        if self.write is False:
            return ""
        self.stats.write("\n" + plateID + " - SKIPPED " + reason + "\n")
        self.summary.write("\n" + plateID + " - SKIPPED " + reason + "\n")


    def close(self):
        if self.write is False:
            return ""
        self.summary.close()
        self.stats.close()
        self.details.close()



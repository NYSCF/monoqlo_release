import os
import numpy as np
import cv2
import datetime

from keras_retinanet.utils.image import preprocess_image, resize_image

import mq_utils
from plate_tracking import plate
from well_tracking import well
from outputs import output

def process_active_plates(dir_path, pmodels, active_plates_file, writefiles=False, crontab=False):
    """
    Parses file detailing which plates to process
    """
    active_plates = [i.strip() for i in open(active_plates_file)][1:]
    run_ids = list(dict.fromkeys([i.split("_")[0] for i in active_plates]))
    for run_id in run_ids:
        run_path = dir_path + run_id + "/"
        process_run(run_path, pmodels, plates=active_plates, writefiles=writefiles, crontab=crontab)



def process_run(run_path, p_models, plates="all", writefiles=False, crontab=False):
    """
    Process single run
    """
    run_name = run_path.split("/")[-2]
    if not os.path.isdir(run_path):
        return print("NO SCANS EXIST FOR", run_name, "- RUN SKIPPED")
    out_files = output(run_name, writefiles=writefiles)
    cc_path = "DS_SS/"

    run_plates = {}
    if not os.path.isdir(cc_path):
        os.mkdir(cc_path)
    mq_utils.add_runs_dates(run_path)
    plate_IDs, image_list = mq_utils.enumerateRunDir(run_path)
    for plate_ID in plate_IDs:
        full_plate_ID = run_name + "_" + plate_ID
        if plates is not "all" and full_plate_ID not in plates:
            out_files.skip(full_plate_ID, "a")
            continue
        current_plate = plate(plate_ID, image_list)

        run_plates[plate_ID] = process_plate(image_list, plate_ID, p_models, out_files, current_plate, run_name, cc_path)
        out_files.write_stats(current_plate.get_stats(), plate_ID)
    out_files.close()


def process_plate(image_list, plate_id, p_models, out_files, current_plate, run_id, ss_path=""):
    """
    Process single plate
    """
    plate_map_classes = {}
    for well_id in current_plate.get_wells():
        picks_path = ""  # file indicating wells that have already been passaged/consolidated (optional)
        if os.path.isfile(picks_path):
            consolidated = [i.split(",")[0] + "_" + i.split(",")[1] for i in open(picks_path)]
        else:
            consolidated = []
        well_results = process_well(image_list, run_id, plate_id, well_id, p_models, consolidated, ss_path=ss_path)
        plate_map_classes[well_id], size, latest_date, classifier_results, coord_info = well_results
        out_files.add_well(plate_id, well_id, plate_map_classes[well_id], latest_date, classifier_results, coord_info, run_id)
        current_plate.add_result(plate_map_classes[well_id], size)

    return plate_map_classes


def process_well(image_list, run_id, plate_id, well_id, pmodels, consolidated, day="choose_latest", ss_path=""):
    """
    Process single well (multiple images)
    """
    if run_id + "_" + plate_id + "_" + well_id in consolidated:
        print("SKIPPING " + run_id + "_" + plate_id + "_" + well_id + " - ALREADY CONSOLIDATED\n")
        return ["consolidated", "NA", "NA", "NA", "NA"]
    current_well = well(image_list, plate_id, well_id)
    well_imgs = current_well.get_paths()
    crop_coords = [0, 0, 0, 0]
    if day is "choose_latest":  # Default value. Pass argument for alternate
        day = len(well_imgs) - 1
    latest_date = well_imgs[day].split("/")[-1].split("_")[3]
    while current_well.is_identified() is False:
        fov = current_well.get_current_fov()
        img_results = process_image(well_imgs[day], day, len(well_imgs), fov, pmodels)
        current_well.add_result(img_results, day)
        size = img_results[4]

        if ss_path is not "":  # Path to save subset images to
            if ss_path[-1] is not "/":
                ss_path += "/"
            draw = img_results[2]
            if day == len(well_imgs) - 1:
                folder_name = "Initial_Detection"
            else:
                folder_name = str(day)
            if not os.path.isdir(ss_path + run_id):
                os.mkdir(ss_path + run_id)
            if not os.path.isdir(ss_path + run_id + "/" + folder_name):
                os.mkdir(ss_path + run_id + "/" + folder_name)

            if not img_results[0] == "empty" or not day == len(well_imgs) - 1:
                draw_file_path = ss_path + run_id + "/" + folder_name + "/" + well_imgs[day].split("/")[-1]
                cv2.imwrite(draw_file_path.split(".")[0] + ".jpg", draw)

        if crop_coords == [0, 0, 0, 0]:
            crop_coords = img_results[5]
            coord_info = {"dimx": crop_coords[2] - crop_coords[0], "dimy": crop_coords[3] - crop_coords[1],
                          "xmin": crop_coords[0], "ymin": crop_coords[1],
                          "xmax": crop_coords[2], "ymax": crop_coords[3]}
            classifier_results = classify_crop(well_imgs[day], crop_coords, pmodels)
        if day == 0:
            current_well.compute_d0_clonal()
        day -= 1

    return [current_well.output_class(), size, latest_date, classifier_results, coord_info]


def process_image(imgpath, day, total_days, fov, pmodels):
    """
    Process a single image
    """
    img = cv2.imread(imgpath, 0)
    img_dim = img.shape
    indent = [0, 0, 0, 0]  # Initialize as all 0s
    if fov == [0, 0, 0, 0]:  # FOV is initialized as [0, 0, 0, 0]
        img, indent = mq_utils.crop_edges(img)
    else:
        img = img[fov[1]: fov[3], fov[0]: fov[2]]
    draw = img.copy()
    draw = cv2.cvtColor(draw, cv2.COLOR_GRAY2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = preprocess_image(img)
    img, scale = resize_image(img)

    if day == 0:
        boxes, scores, labels = pmodels[2].predict_on_batch(np.expand_dims(img, axis=0))
    elif day == total_days - 1:
        boxes, scores, labels = pmodels[0].predict_on_batch(np.expand_dims(img, axis=0))
    else:
        boxes, scores, labels = pmodels[1].predict_on_batch(np.expand_dims(img, axis=0))

    boxes = (boxes / scale).astype(int)
    col_count = mq_utils.get_col_count(boxes, scores, labels)
    print(str(col_count) + " colonies detected in " + imgpath.split("/")[-1] + " (day " + str(day) + ")")

    draw = mq_utils.draw_all_detections(draw, boxes, scores, labels)

    coord_list = mq_utils.parse_col_coords(fov, [boxes, scores, labels])
    full_coords = mq_utils.parse_full_coords(fov, [boxes, scores, labels])

    classification, col_count = mq_utils.compute_class(boxes, scores, labels, day, fov, coord_list)
    new_fov = mq_utils.get_new_fov(fov, [boxes, scores, labels], indent, img_dim, day)
    if classification == "monoclonal":
        size = mq_utils.get_col_size([boxes, scores, labels])
    else:
        size = 0
    return [classification, new_fov, draw, coord_list, size, full_coords]


def classify_crop(imgpath, coords, pmodels):
    # Placeholder for classification model results
    return ["-", "-", "-", "-", "-"]

def classify_crop_placeholder(imgpath, coords, pmodels):
    ### Currently unused (but usable) instance of "classify crop" - names can be switched in order to use
    if coords == [0, 0, 0, 0]:
        return ["-", "-", "-", "-", "-"]
    img = cv2.imread(imgpath, 0)
    img, indents = mq_utils.crop_edges(img)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    img = img[coords[1]: coords[3],
              coords[0]: coords[2]]
    img = cv2.resize(img, (400, 400))
    img = img.astype("float") / 255.0
    imgs = [img]
    imgs = np.array(imgs)
    pred = pmodels[3].predict(imgs)
    max_index = list(pred[0]).index(max(list(pred[0])))
    cm1, cm2, cm3, cm4 = list(pred[0])
    colony_class = "M" + str(max_index + 1)
    print("Colony class - " + colony_class)
    return [colony_class, cm1, cm2, cm3, cm4]
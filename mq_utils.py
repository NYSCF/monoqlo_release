import cv2
import os, math
import numpy as np

import datetime

def enumerateRunDir(path):
    """
    Searches run directory for images
    Enumerates all plates and available scans
    Assumes earliest date is day 1 scan
    Runs and dates must be appended to file names
    """
    uniquePlateIDs = []
    imagePaths = []
    for plate in os.listdir(path):
        if plate.split("_")[1] + "_" + plate.split("_")[2] not in uniquePlateIDs:  # Plate ID
            uniquePlateIDs.append(plate.split("_")[1] + "_" + plate.split("_")[2])
        for well in os.listdir(path + plate):
            imagePaths.append(path + plate + "/" + well)
    print("[INFO]Directory totals " + str(len(uniquePlateIDs)) +
            " plates and " + str(len(imagePaths)) + " images.")
    uniquePlateIDs.sort()
    imagePaths.sort()
    return[uniquePlateIDs, imagePaths]


def add_runs_dates(path):
    """
    Appends the run name and date to image file names
    """
    for scan in os.listdir(path):
        for wellimg in os.listdir(path + scan):
            if wellimg[0:4] == "Well":
                print("Renaming " +
                      path + scan + "/" + wellimg + " to " +
                      path + scan + "/" + scan + "__" + wellimg
                      )
                os.rename(path + scan + "/" + wellimg,
                          path + scan + "/" + scan + "__" + wellimg)


def get_sep_ratio(box1, box2):
    """
    Returns the separation ratio between two boxes:
    Distance between two centers : average edge length
    """
    import math
    center1_x = box1[0] + 0.5 * (box1[2] - box1[0])
    center1_y = box1[1] + 0.5 * (box1[3] - box1[1])
    center2_x = box2[0] + 0.5 * (box2[2] - box2[0])
    center2_y = box2[1] + 0.5 * (box2[3] - box2[1])
    avg_side = (
                max(box1[2] - box1[0], box2[2] - box2[0]) +
                max(box1[3] - box1[1], box2[3] - box2[1])
                                                        ) / 2
    x_dist_sq = math.pow(abs(center1_x - center2_x), 2)
    y_dist_sq = math.pow(abs(center1_y - center2_y), 2)
    dist = math.sqrt(x_dist_sq + y_dist_sq)
    return dist / avg_side


def compute_class(boxes, scores, labels, day, fov, coord_list):
    """
    Computes class for a single image result
    """
    col_count = 0
    diff = False
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        o_xmin, o_ymin, o_xmax, o_ymax = box.astype(int)  ### Object coords
        if score < 0.5:
            break
        if label == 0:
            col_count += 1
        elif label == 2:
            diff = True

    if diff:
        classification = "diff"
    else:
        if len(coord_list) == 1:
            classification = "mono"
        elif len(coord_list) > 1:
            classification = "poly"
        else:
            classification = "empty"

    return [classification, col_count]


def get_coords_from_path(imgpath):
    try:
        filename = imgpath.split("/")[-1]
        coords = filename.split("__")[-1].split(".")[0].split("--")
        coords_int = []
        for i in coords:
            coords_int.append(eval(i))
    except NameError:
        return [0, 0, 0, 0]
    return coords_int

def get_new_fov(prev_fov, image_results, indent, img_dims, day):
    boxes, scores, labels = image_results[0], image_results[1], image_results[2]
    c_xmins, c_xmaxes, c_ymins, c_ymaxes = [], [], [], []
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        if score < 0.5:
            break
        c_xmin, c_ymin, c_xmax, c_ymax = box.astype(int)

        c_xmins.append(c_xmin)
        c_ymins.append(c_ymin)
        c_xmaxes.append(c_xmax)
        c_ymaxes.append(c_ymax)

    if len(c_xmins) == 0:
        return prev_fov

    c_xmin, c_ymin = min(c_xmins), min(c_ymins)
    c_xmax, c_ymax = max(c_xmaxes), max(c_ymaxes)
    colony_xdim, colony_ydim = c_xmax - c_xmin, c_ymax - c_ymin

    xmin, ymin, xmax, ymax = prev_fov

    xmin += c_xmin + indent[0]
    ymin += c_ymin + indent[1]
    xmax = xmin + (c_xmax - c_xmin)
    ymax = ymin + (c_ymax - c_ymin)
    if day < 5:
        enlargement_factor = 4
    else:
        enlargement_factor = 3
    while (xmax - xmin < img_dims[1] - indent[2]) and (xmax - xmin < enlargement_factor * colony_xdim):
        if xmin > 0:
            xmin -= 1
        if xmax < img_dims[1] - indent[2]:
            xmax += 1
    while (ymax - ymin < img_dims[0] - indent[3] and (ymax - ymin < enlargement_factor * colony_ydim)):
        if ymin > 0:
            ymin -= 1
        if ymax < img_dims[0] - indent[3]:
            ymax += 1

    return [xmin, ymin, xmax, ymax]


def crop_edges(img):
    """
    Crops black edges from a full Celigo image
    Must be read in grayscale (single-channel)
    """
    imarray = np.array(img)
    slideIndex = [0, len(imarray) - 1, 0, len(imarray[0]) - 1]
    left_indent, top_indent, right_indent, bottom_indent = [0, 0, 0, 0]
    pixel_threshold = 70
    while np.max(imarray[slideIndex[0]]) <= pixel_threshold:
      top_indent += 1
      slideIndex[0] += 1
    while np.max(imarray[slideIndex[1]]) <= pixel_threshold:
      bottom_indent += 1
      slideIndex[1] -= 1
    while np.max(imarray.T[slideIndex[2]]) <= pixel_threshold:
      left_indent += 1
      slideIndex[2] += 1
    while np.max(imarray.T[slideIndex[3]]) <= pixel_threshold:
      right_indent += 1
      slideIndex[3] -= 1

    slidedImarray = imarray[
      slideIndex[0]: slideIndex[1],
      slideIndex[2]: slideIndex[3]]

    indents = [left_indent, top_indent, right_indent, bottom_indent]

    # Returning slide index allows us to keep track of how far the image was cropped
    return [slidedImarray, indents]

def draw_all_detections(draw, boxes, scores, labels):
    """
    Takes in a numpy array image
    Draws bounding boxes for all CNN object detections
    """
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        o_xmin, o_ymin, o_xmax, o_ymax = box.astype(int)  ### Object coords
        if score < 0.5:
            break
        if label == 0:
            draw = cv2.rectangle(draw, (o_xmin, o_ymin), (o_xmax, o_ymax), (0, 255, 0), 3)
        elif label == 2:
            draw = cv2.rectangle(draw, (o_xmin, o_ymin), (o_xmax, o_ymax), (0, 0, 255), 3)

    return draw


def combine_boxes(b1, b2):
    xmin = min(b1[0], b2[0])
    ymin = min(b1[1], b2[1])
    xmax = max(b1[2], b2[2])
    ymax = max(b1[3], b2[3])

    return [xmin, ymin, xmax, ymax]


def parse_col_coords(fov, results):
    boxes, scores, labels = results
    coord_list = []
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        o_xmin, o_ymin, o_xmax, o_ymax = box.astype(int)  ### Object coords
        if score < 0.5:
            break
        if label == 0:
            b = [box.astype(int)[0] + fov[0], box.astype(int)[1] + fov[1],
                 fov[0] + box.astype(int)[0] + (box.astype(int)[2] - box.astype(int)[0]),
                 fov[1] + box.astype(int)[1] + (box.astype(int)[3] - box.astype(int)[1]), ]
            if len(coord_list) == 0:
                coord_list.append(b)
            else:
                for idx in range(len(coord_list)):
                    print("\tProximity comparison - " + str(b) + " to " + str(coord_list[idx]) + ". SR - " +
                          str(get_sep_ratio(b, coord_list[idx])))
                    print("\t\tSeparation ratio - " + str(get_sep_ratio(b, coord_list[idx])))
                    if get_sep_ratio(b, coord_list[idx]) < 0.9:
                        print("\t\tCombining.")
                        coord_list[idx] = combine_boxes(b, coord_list[idx])
                    else:
                        print("\t\tDeclaring as separate colonies.")
                        coord_list.append(b)
                        # coord_list.append([fov[0] + o_xmin, fov[1] + o_ymin,
                        #                    fov[2] + o_xmin, fov[3] + o_xmin])

    return coord_list

def parse_full_coords(fov, results):
    boxes, scores, labels = results
    xmins, ymins, xmaxes, ymaxes = [], [], [], []
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        if score < 0.5:
            break
        o_xmin, o_ymin, o_xmax, o_ymax = box.astype(int)  ### Object coords
        xmins.append(o_xmin)
        ymins.append(o_ymin)
        xmaxes.append(o_xmax)
        ymaxes.append(o_ymax)

    if len(xmins) > 0:
        return [fov[0] + min(xmins), fov[1] + min(ymins),
                fov[2] + max(xmaxes), fov[3] + max(ymaxes)]
    else:
        return [0, 0, 0, 0]

def is_same_colony(coords, latter_coords, day):  # E + L = Early + Late, respectively
    """
    CURRENTLY NOT FUNCTIONAL OR IN USE
    Returns a boolean indicating whether 2 object detections represents the same colony
    """
    center_e = [coords[0] + 0.5 * (coords[2] - coords[0]),
                coords[1] + 0.5 * (coords[3] - coords[1])]
    center_l = [latter_coords[0] + 0.5 * (latter_coords[2] - latter_coords[0]),
                latter_coords[1] + 0.5 * (latter_coords[3] - latter_coords[1])]
    c2c_dist = math.pow(
               math.pow(abs(center_e[0] - center_l[0]), 2) +
               math.pow(abs(center_e[1] - center_l[1]), 2),
               0.5)
    # Horizontal and vertical deviation ratios
    c1x, c1y = coords[0] + 0.5 * (coords[2] - coords[0]), \
               coords[1] + 0.5 * (coords[3] - coords[1])
    c2x, c2y = latter_coords[0] + 0.5 * (latter_coords[2] - latter_coords[0]), \
               latter_coords[1] + 0.5 * (latter_coords[3] - latter_coords[1])

    dev_rat_hrz = abs(c1x - c2x) / abs(latter_coords[2] - latter_coords[0])
    dev_rat_vrt = abs(c1y - c2y) / abs(latter_coords[3] - latter_coords[1])

    ### Regularize against current day (earlier days yield higher ratios otherwise)
    #dev_rat_hrz *= math.sqrt(day)
    #dev_rat_vrt *= math.sqrt(day)
    print("\t\tHorizontal deviation ratio - " + str(dev_rat_hrz))
    print("\t\tVertical deviation ratio - " + str(dev_rat_vrt))

    if dev_rat_hrz > 1:
        print("\t\tNot same colony. Deviates too far in the horizontal. Ratio - " + str(dev_rat_hrz))
        return False
    if dev_rat_vrt > 1:
        print("\t\tNot same colony. Deviates too far in the Vertical. Ratio - " + str(dev_rat_vrt))
        return False
    print("\t\tSame colony found")
    return True

def get_sorted_scans(imageList, plateID, well):
    """
    Sorts scan names by date for a given plate and well ID
    Returns ordered list
    Restricts to max 1 scan per calendar day
    """
    filteredScans = []
    dates = []
    years = []
    months = []
    for i in imageList:
        date = "-".join(i.split("/")[-2].split("_")[3].split("-")[0:3])
        if date in dates:
            continue
        if "_" + plateID in i and "Well_" + well + "_" in i:
            dates.append(date)
            filteredScans.append(i)
        if i.split("/")[-2].split("_")[3].split("-")[2] not in years:
            years.append(i.split("/")[-2].split("_")[3].split("-")[2])
        if int(i.split("/")[-2].split("_")[3].split("-")[0]) not in months:
            months.append(int(i.split("/")[-2].split("_")[3].split("-")[0]))
    filteredScans.sort()
    daySortedScans = []
    for i in filteredScans:
        if len(i.split("/")[-2].split("_")[3].split("-")[1]) == 1:
            daySortedScans.append(i)
    for i in filteredScans:
        if len(i.split("/")[-2].split("_")[3].split("-")[1]) == 2:
            daySortedScans.append(i)
    months.sort()
    monthSortedScans = []
    for month in months:
        for i in daySortedScans:
            if int(i.split("/")[-2].split("_")[3].split("-")[0]) == month:
                monthSortedScans.append(i)
    if len(years) == 2:
        year1, year2 = min(years), max(years)
        yearSortedScans = []
        for i in monthSortedScans:
            if i.split("/")[-2].split("_")[3].split("-")[2] == year1:
                yearSortedScans.append(i)
        for i in monthSortedScans:
            if i.split("/")[-2].split("_")[3].split("-")[2] == year2:
                yearSortedScans.append(i)
        return yearSortedScans
    else:
        return monthSortedScans

def is_within(box_e, box_l):  # Boxes earlier and later
    '''
    CURRENTLY NOT IN USE
    Returns a boolean indicating whether one box is within another
    '''
    l_xdim = box_l[2] - box_l[0]
    l_ydim = box_l[3] - box_l[1]
    if box_e[0] < (box_l[0] - 0.5 * l_xdim) or box_e[1] < (box_l[1] - 0.5 * l_ydim):
        return False
    if box_e[2] > (box_l[2] + 0.5 * l_xdim) or box_e[3] > (box_l[3] + 0.5 * l_ydim):
        return False
    return True


def get_col_count(boxes, scores, labels):
    cc = 0
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        if score < 0.5:
            break
        if label == 0:
            cc += 1
    return cc

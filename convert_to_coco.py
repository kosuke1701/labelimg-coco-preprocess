from argparse import Namespace, ArgumentParser
import glob
import json
import ntpath
import os
import shutil
import sys
import xml.etree.ElementTree as ET

from tqdm import tqdm

def load_voc_bbox(fn):
    info = Namespace()

    tree = ET.parse(fn)
    root = tree.getroot()

    # Image information
    info.image_fn = root.find("path").text
    info.width = int(root.find("size").find("width").text)
    info.height = int(root.find("size").find("height").text)

    # Bounding boxes
    objects = []
    for obj in root.findall("object"):
        label = obj.find("name").text
        bbox = obj.find("bndbox")
        xmin = int(bbox.find("xmin").text)
        ymin = int(bbox.find("ymin").text)
        xmax = int(bbox.find("xmax").text)
        ymax = int(bbox.find("ymax").text)

        objects.append(Namespace(label=label, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax))
    info.objects = objects

    return info

if __name__=="__main__":
    parser = ArgumentParser()

    parser.add_argument("--annotation-fn", type=str, help="Filename of annotation JSON file.")
    parser.add_argument("--copy-images", action="store_true", help="Copy images or not.")
    parser.add_argument("--image-root-dir", type=str, default=None, help="Images will be copied into this directory.")
    parser.add_argument("--annotation-dir", type=str, nargs="+", help="Annotation XML files are recursively searched from these directories.")
    parser.add_argument("--same-dir", action="store_true", help="Image file is in same directory as an annotation file.")
    parser.add_argument("--id-fn", type=str, help="Each line of this file contains label names.")

    args = parser.parse_args()

    # Get list of all annotation files.
    all_annotation_files = []
    for directory in args.annotation_dir:
        all_annotation_files += glob.glob(
            os.path.join(directory, "**", "*.xml")
        )
        all_annotation_files += glob.glob(
            os.path.join(directory, "*.xml")
        )
    
    if not os.path.exists(args.image_root_dir):
        os.makedirs(args.image_root_dir)

    cat2id = {}
    with open(args.id_fn) as h:
        for line in h:
            line = line.replace("\n", "")
            if len(line) > 0:
                cat2id[line] = len(cat2id)

    images = []
    annotations = []
    image_suffix = ["jpg", "png"]
    for xml_fn in tqdm(all_annotation_files):
        info = load_voc_bbox(xml_fn)

        # Image information
        image_id = len(images)
        if "\\" in info.image_fn:
            image_base_fn = ntpath.basename(info.image_fn)
        else:
            image_base_fn = os.path.basename(info.image_fn)
        suffix = image_base_fn.split(".")[-1].lower()
        if suffix not in image_suffix:
            continue
        if args.copy_images:
            if args.same_dir:
                image_fn = os.path.join(os.path.dirname(xml_fn), image_base_fn)
            else:
                image_fn = info.image_fn
            shutil.copy(image_fn, f"{args.image_root_dir}/{image_base_fn}")
        
        images.append({
            "file_name": image_base_fn,
            "height": info.height,
            "width": info.width,
            "id": image_id
        })

        # Annotation information
        for obj in info.objects:
            if obj.label not in cat2id:
                raise Exception(f"ID is not defined for {obj.label}")
            cat_id = cat2id[obj.label]

            annotations.append({
                "image_id": image_id,
                "bbox": [obj.xmin, obj.ymin, obj.xmax - obj.xmin, obj.ymax - obj.ymin],
                "category_id": cat_id + 1, # Category ID is zero indexed!!
                "id": len(annotations),
                "iscrowd": 0,
                "area": (obj.xmax - obj.xmin) * (obj.ymax - obj.ymin)
            })
    
    # Categories
    categories = []
    for cat_name, cat_id in cat2id.items():
        row = cat_name.split(".")
        assert len(row) > 0
        if len(row) == 1:
            row.append(row[0])
        elif len(row) > 1:
            row = [row[0], ".".join(row[1:])]

        categories.append({
            "supercategory": row[0],
            "name": row[1],
            "id": cat_id + 1
        })
    
    # Save annotation file
    json.dump(
        {"images": images, "annotations": annotations, "categories": categories},
        open(args.annotation_fn, "w")
    )

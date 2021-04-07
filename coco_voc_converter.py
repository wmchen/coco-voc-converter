"""
Transfer between COCO annotation fashion and VOC annotation fashion
Programmer: Weiming Chen
Date: 2021.3
"""
import os
import argparse
import json
from xml.dom.minidom import Document
import xml.etree.ElementTree as ET
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description='Transfer between COCO annotation fashion and VOC annotation fashion')
    parser.add_argument('src',
                        help='The source file or directory.')
    parser.add_argument('dst',
                        help='The destination file or directory.')
    parser.add_argument('--voc2coco', action='store_true', help='Transfer VOC annotation fashion into COCO fashion')
    parser.add_argument('--coco2voc', action='store_true', help='Transfer COCO annotation fashion into VOC fashion')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    assert not (args.voc2coco and args.coco2voc), 'Can not operate VOC to COCO and COCO to VOC simultaneously'
    if args.voc2coco:
        voc2coco(args.src, args.dst)
    if args.coco2voc:
        coco2voc(args.src, args.dst)


def coco2voc(src, dst):
    """
    Transfer COCO annotation fashion into VOC fashion
    Args:
        src (str): source file (json)
        dst (str): destination directory
    """
    if not os.path.exists(dst):
        dst_dir = os.path.abspath(dst)
        os.mkdir(dst_dir)
        print(f'create directory: {dst_dir}')
    else:
        dst_dir = dst

    if not os.path.isfile(src):
        raise FileNotFoundError('COCO to VOC must input a file as source.')
    if not os.path.isdir(dst_dir):
        raise NotADirectoryError('COCO to VOC must input a directory as destination.')

    with open(src, 'r') as f:
        coco_ann = json.load(f)

    for img_info in coco_ann['images']:
        filename = img_info['file_name']
        width = img_info['width']
        height = img_info['height']
        depth = img_info['depth']
        img_id = img_info['id']

        doc = Document()
        root = doc.createElement('annotation')
        doc.appendChild(root)

        filename_node = doc.createElement('filename')
        filename_text = doc.createTextNode(filename)
        filename_node.appendChild(filename_text)
        root.appendChild(filename_node)

        size_node = doc.createElement('size')
        width_node = doc.createElement('width')
        width_text = doc.createTextNode(str(width))
        width_node.appendChild(width_text)
        height_node = doc.createElement('height')
        height_text = doc.createTextNode(str(height))
        height_node.appendChild(height_text)
        depth_node = doc.createElement('depth')
        depth_text = doc.createTextNode(str(depth))
        depth_node.appendChild(depth_text)
        size_node.appendChild(width_node)
        size_node.appendChild(height_node)
        size_node.appendChild(depth_node)
        root.appendChild(size_node)

        del_list = []
        for ann in coco_ann['annotations']:
            if ann['image_id'] == img_id:
                del_list.append(ann)
                name = ann['name']
                pose = ann['pose']
                truncated = ann['truncated']
                difficult = ann['difficult']
                xmin = ann['bbox'][0]
                ymin = ann['bbox'][1]
                w = ann['bbox'][2]
                h = ann['bbox'][3]
                xmax = xmin + w
                ymax = ymin + h
                object_node = doc.createElement('object')
                type_node = doc.createElement('type')
                type_text = doc.createTextNode('bndbox')
                type_node.appendChild(type_text)
                name_node = doc.createElement('name')
                name_text = doc.createTextNode(name)
                name_node.appendChild(name_text)
                pose_node = doc.createElement('pose')
                pose_text = doc.createTextNode(pose)
                pose_node.appendChild(pose_text)
                truncated_node = doc.createElement('truncated')
                truncated_text = doc.createTextNode(str(truncated))
                truncated_node.appendChild(truncated_text)
                difficult_node = doc.createElement('difficult')
                difficult_text = doc.createTextNode(str(difficult))
                difficult_node.appendChild(difficult_text)
                bndbox_node = doc.createElement('bndbox')
                xmin_node = doc.createElement('xmin')
                xmin_text = doc.createTextNode(str(xmin))
                xmin_node.appendChild(xmin_text)
                xmax_node = doc.createElement('xmax')
                xmax_text = doc.createTextNode(str(xmax))
                xmax_node.appendChild(xmax_text)
                ymin_node = doc.createElement('ymin')
                ymin_text = doc.createTextNode(str(ymin))
                ymin_node.appendChild(ymin_text)
                ymax_node = doc.createElement('ymax')
                ymax_text = doc.createTextNode(str(ymax))
                ymax_node.appendChild(ymax_text)
                bndbox_node.appendChild(xmin_node)
                bndbox_node.appendChild(ymin_node)
                bndbox_node.appendChild(xmax_node)
                bndbox_node.appendChild(ymax_node)
                object_node.appendChild(type_node)
                object_node.appendChild(name_node)
                object_node.appendChild(pose_node)
                object_node.appendChild(truncated_node)
                object_node.appendChild(difficult_node)
                object_node.appendChild(bndbox_node)
                root.appendChild(object_node)
        for del_item in del_list:
            coco_ann['annotations'].remove(del_item)

        xml_name = filename.split('.')[0] + '.xml'
        with open(os.path.join(dst_dir, xml_name), 'w') as f:
            f.write(doc.toprettyxml())


def voc2coco(src, dst):
    """
    Transfer VOC annotation fashion into COCO fashion
    Args:
        src (str): source directory
        dst (str): destination directory
    """
    if not os.path.isdir(src):
        raise NotADirectoryError('VOC to COCO must input a directory as source.')
    if not os.path.isdir(dst):
        raise NotADirectoryError('VOC to COCO must input a directory as destination.')

    voc_ann, label_set = load_voc_annotation(src)

    coco_ann = {
        'images': [],
        'annotations': [],
        'categories': []
    }
    for i, label in enumerate(label_set):
        coco_ann['categories'].append(
            {
                'supercategory': None,
                'id': i + 1,
                'name': label
            }
        )
    annotation_id = 0
    for i, ann in enumerate(voc_ann):
        coco_ann['images'].append(
            {
                'file_name': ann['image_info']['filename'],
                'width': ann['image_info']['width'],
                'height': ann['image_info']['height'],
                'depth': ann['image_info']['depth'],
                'id': i,
            }
        )
        for ann_detail in ann['ann']:
            for cat in coco_ann['categories']:
                if ann_detail['label'] == cat['name']:
                    category_id = cat['id']
                    break
            xmin = ann_detail['bbox'][0]
            ymin = ann_detail['bbox'][1]
            xmax = ann_detail['bbox'][2]
            ymax = ann_detail['bbox'][3]
            width = xmax - xmin
            height = ymax - ymin
            area = float(width * height)
            bbox = [xmin, ymin, width, height]
            coco_ann['annotations'].append(
                {
                    'id': annotation_id,
                    'image_id': i,
                    'name': ann_detail['label'],
                    'category_id': category_id,
                    'bbox': bbox,
                    'area': area,
                    'segmentation': None,
                    'iscrowd': 0,
                    'pose': ann_detail['pose'],
                    'truncated': ann_detail['truncated'],
                    'difficult': ann_detail['difficult']
                }
            )
            annotation_id += 1
    now_time = datetime.now().strftime('%Y%m%d%H%M%S')
    save_file = f'voc2coco_{now_time}.json'
    with open(os.path.join(dst, save_file), 'w') as f:
        json.dump(coco_ann, f)


def load_voc_annotation(voc_ann_dir):
    """
    Load all the annotation files from VOC dataset.
    Args:
        voc_ann_dir (str): the directory of VOC annotation files.
    """
    ann_files = os.listdir(voc_ann_dir)
    all_ann = []
    label_set = []
    for i, file in enumerate(ann_files):
        tree = ET.parse(os.path.join(voc_ann_dir, file))
        root = tree.getroot()

        ann = {
            'image_info': {},
            'ann': []
        }
        filename = root.find('filename').text
        width = int(root.find('size').find('width').text)
        height = int(root.find('size').find('height').text)
        depth = int(root.find('size').find('depth').text)
        ann['image_info'] = {
            'filename': filename,
            'width': width,
            'height': height,
            'depth': depth,
        }

        for obj in root.iter('object'):
            label_name = obj.find('name').text
            if label_name not in label_set:
                label_set.append(label_name)
            pose = obj.find('pose').text
            truncated = int(obj.find('truncated').text)
            difficult = int(obj.find('difficult').text)
            bbox = [
                int(obj.find('bndbox').find('xmin').text),
                int(obj.find('bndbox').find('ymin').text),
                int(obj.find('bndbox').find('xmax').text),
                int(obj.find('bndbox').find('ymax').text),
            ]  # [xmin, ymin, xmax, ymax]
            ann['ann'].append(
                {
                    'label': label_name,
                    'pose': pose,
                    'truncated': truncated,
                    'difficult': difficult,
                    'bbox': bbox,
                }
            )
        all_ann.append(ann)
    return all_ann, label_set


if __name__ == '__main__':
    main()

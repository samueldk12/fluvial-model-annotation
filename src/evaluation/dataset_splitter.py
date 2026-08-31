import os
import re
import json
from collections import defaultdict

class TemporalDatasetSplitter:
    def __init__(self, val_ratio=0.20, test_ratio=0.10, seed=42):
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    @staticmethod
    def extract_date_key(image_info):
        created_at = image_info.get('created_at', '')
        if created_at:
            match = re.search(r'(\d{4}-\d{2}-\d{2})', str(created_at))
            if match:
                return match.group(1)
            match_compact = re.search(r'(\d{4})(\d{2})(\d{2})', str(created_at))
            if match_compact:
                return match_compact.group(1) + '-' + match_compact.group(2) + '-' + match_compact.group(3)

        filename = image_info.get('file_name', image_info.get('filename', ''))
        match_fn = re.search(r'(\d{4})(\d{2})(\d{2})', str(filename))
        if match_fn:
            return match_fn.group(1) + '-' + match_fn.group(2) + '-' + match_fn.group(3)

        match_date_fn = re.search(r'(\d{4}-\d{2}-\d{2})', str(filename))
        if match_date_fn:
            return match_date_fn.group(1)

        source_video = image_info.get('source_video', '')
        match_src = re.search(r'(\d{4})(\d{2})(\d{2})', str(source_video))
        if match_src:
            return match_src.group(1) + '-' + match_src.group(2) + '-' + match_src.group(3)

        return 'undated_session_default'

    def split_coco_dataset(self, coco_dict):
        images = coco_dict.get('images', [])
        annotations = coco_dict.get('annotations', [])
        categories = coco_dict.get('categories', [])

        images_by_day = defaultdict(list)
        for img in images:
            day_key = self.extract_date_key(img)
            images_by_day[day_key].append(img)

        sorted_days = sorted(list(images_by_day.keys()))
        n_days = len(sorted_days)

        if n_days == 1:
            train_days = sorted_days
            val_days = sorted_days
            test_days = sorted_days
        elif n_days == 2:
            train_days = [sorted_days[0]]
            val_days = [sorted_days[1]]
            test_days = [sorted_days[1]]
        else:
            n_test = max(1, int(round(n_days * self.test_ratio)))
            n_val = max(1, int(round(n_days * self.val_ratio)))
            n_train = max(1, n_days - n_val - n_test)

            train_days = sorted_days[:n_train]
            val_days = sorted_days[n_train:n_train + n_val]
            test_days = sorted_days[n_train + n_val:]

        train_imgs = [img for d in train_days for img in images_by_day[d]]
        val_imgs = [img for d in val_days for img in images_by_day[d]]
        test_imgs = [img for d in test_days for img in images_by_day[d]]

        train_img_ids = {img['id'] for img in train_imgs}
        val_img_ids = {img['id'] for img in val_imgs}
        test_img_ids = {img['id'] for img in test_imgs}

        train_anns = [a for a in annotations if a['image_id'] in train_img_ids]
        val_anns = [a for a in annotations if a['image_id'] in val_img_ids]
        test_anns = [a for a in annotations if a['image_id'] in test_img_ids]

        return {
            'train': {
                'images': train_imgs,
                'annotations': train_anns,
                'categories': categories,
                'days': train_days
            },
            'val': {
                'images': val_imgs,
                'annotations': val_anns,
                'categories': categories,
                'days': val_days
            },
            'test': {
                'images': test_imgs,
                'annotations': test_anns,
                'categories': categories,
                'days': test_days
            },
            'summary': {
                'total_days': n_days,
                'days_by_split': {
                    'train': train_days,
                    'val': val_days,
                    'test': test_days
                },
                'images_count': {
                    'train': len(train_imgs),
                    'val': len(val_imgs),
                    'test': len(test_imgs)
                },
                'annotations_count': {
                    'train': len(train_anns),
                    'val': len(val_anns),
                    'test': len(test_anns)
                }
            }
        }

    def convert_manifest_to_coco(self, manifest_dict_or_path):
        if isinstance(manifest_dict_or_path, str):
            with open(manifest_dict_or_path, 'r', encoding='utf-8') as f:
                raw_manifest = json.load(f)
        else:
            raw_manifest = manifest_dict_or_path

        categories_map = {}
        images = []
        annotations = []
        ann_idx = 1

        for item_id, item in raw_manifest.items():
            img_id = item.get('id', item_id)
            w = item.get('width', 1280)
            h = item.get('height', 720)
            fn = item.get('filename', str(img_id) + '.jpg')
            created_at = item.get('created_at', '')
            src_video = item.get('source_video', '')

            images.append({
                'id': img_id,
                'file_name': fn,
                'width': w,
                'height': h,
                'created_at': created_at,
                'source_video': src_video
            })

            boxes = item.get('boxes', [])
            for b in boxes:
                cls_name = b.get('class_name', 'embarcacao')
                if cls_name not in categories_map:
                    categories_map[cls_name] = len(categories_map)

                cid = categories_map[cls_name]
                x1 = float(b.get('x1', 0))
                y1 = float(b.get('y1', 0))
                x2 = float(b.get('x2', 0))
                y2 = float(b.get('y2', 0))
                bw = max(0.0, x2 - x1)
                bh = max(0.0, y2 - y1)

                annotations.append({
                    'id': ann_idx,
                    'image_id': img_id,
                    'category_id': cid,
                    'bbox': [x1, y1, bw, bh],
                    'area': bw * bh,
                    'iscrowd': 0
                })
                ann_idx += 1

        categories = [{'id': cid, 'name': cname} for cname, cid in categories_map.items()]
        if not categories:
            categories = [{'id': 0, 'name': 'embarcacao'}]

        return {
            'images': images,
            'annotations': annotations,
            'categories': categories
        }

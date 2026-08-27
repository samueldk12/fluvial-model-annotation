# -*- coding: utf-8 -*-
"""
Gerenciador de Datasets & Anotação de Vídeo para Treinamento YOLO (Detecção e Segmentação).
Persiste imagens e anotações no formato padrão Ultralytics YOLO (BBox e Polígonos de Segmentação),
gerencia o manifesto, importa/continua datasets existentes e permite exportação completa em ZIP.
"""

import os
import sys
import time
import json
import uuid
import shutil
import zipfile
import cv2
import numpy as np


DEFAULT_CLASSES = [
    "embarcacao",
    "navio_cargueiro",
    "rebocador",
    "balsa",
    "lancha",
    "veleiro",
    "boia_sinalizacao",
    "outro"
]


class DatasetAnnotationManager:
    """Gerencia o ciclo de vida das anotações de frames de vídeo e exportação/importação de datasets por domínio."""

    def __init__(self, project_dir, domain_id="naval"):
        self.project_dir = project_dir
        self.domain_id = domain_id
        
        folder_name = "annotated_frames" if domain_id == "naval" else f"annotated_frames_{domain_id}"
        self.dataset_dir = os.path.join(project_dir, "datasets", folder_name)
        self.images_dir = os.path.join(self.dataset_dir, "images")
        self.labels_dir = os.path.join(self.dataset_dir, "labels")
        self.exports_dir = os.path.join(self.dataset_dir, "exports")
        self.manifest_path = os.path.join(self.dataset_dir, "manifest.json")
        self.yaml_path = os.path.join(self.dataset_dir, "data.yaml")

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.labels_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)

        self._init_data_yaml()

    def _init_data_yaml(self):
        """Inicializa ou atualiza o arquivo data.yaml do dataset."""
        classes = self.get_classes()
        dataset_path_clean = os.path.abspath(self.dataset_dir).replace('\\', '/')
        yaml_content = f"""# Dataset YOLO ({self.domain_id}) Gerado pelo Estúdio de Anotação CVAT
path: {dataset_path_clean}
train: images/train
val: images/val

names:
"""
        for idx, c in enumerate(classes):
            yaml_content += f"  {idx}: {c}\n"

        with open(self.yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

    def get_classes(self):
        """Retorna as classes ativas do dataset."""
        cfg_file = os.path.join(self.dataset_dir, "classes.json")
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        from src.domains.domain_config import DOMAINS_CONFIG
        dom_conf = DOMAINS_CONFIG.get(self.domain_id)
        if dom_conf and "classes" in dom_conf:
            return [c["name"] for c in dom_conf["classes"]]
            
        return DEFAULT_CLASSES

    def set_classes(self, classes_list):
        """Atualiza a lista de classes disponíveis."""
        cfg_file = os.path.join(self.dataset_dir, "classes.json")
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(classes_list, f, indent=2, ensure_ascii=False)
        self._init_data_yaml()

    def _load_manifest(self):
        """Carrega o manifesto de anotações."""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_manifest(self, manifest):
        """Salva o manifesto em disco."""
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def save_annotation(self, image_bgr, boxes=None, polygons=None, source_video="video", frame_timestamp=0.0, notes=""):
        """
        Salva um frame de imagem, caixas (BBox) e polígonos de segmentação no formato YOLO.
        boxes: lista de dicts com {"class_id": int, "x1": float, "y1": float, "x2": float, "y2": float}
        polygons: lista de dicts com {"class_id": int, "points": [{"x": float, "y": float}, ...]}
        """
        if boxes is None: boxes = []
        if polygons is None: polygons = []

        h, w = image_bgr.shape[:2]
        image_id = str(uuid.uuid4())[:8]
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        img_filename = f"frame_{timestamp_str}_{image_id}.jpg"
        label_filename = f"frame_{timestamp_str}_{image_id}.txt"

        img_path = os.path.join(self.images_dir, img_filename)
        label_path = os.path.join(self.labels_dir, label_filename)

        # Salva imagem em alta qualidade
        cv2.imwrite(img_path, image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])

        classes = self.get_classes()
        label_lines = []
        normalized_boxes = []
        normalized_polygons = []

        # 1. Processa Bounding Boxes
        for b in boxes:
            cls_id = int(b.get("class_id", 0))
            if cls_id >= len(classes):
                cls_id = 0

            x1 = float(b["x1"])
            y1 = float(b["y1"])
            x2 = float(b["x2"])
            y2 = float(b["y2"])

            x_min = max(0.0, min(x1, x2))
            y_min = max(0.0, min(y1, y2))
            x_max = min(float(w), max(x1, x2))
            y_max = min(float(h), max(y1, y2))

            bw = x_max - x_min
            bh = y_max - y_min
            if bw <= 1 or bh <= 1:
                continue

            cx = (x_min + x_max) / 2.0
            cy = (y_min + y_max) / 2.0

            n_cx = cx / w
            n_cy = cy / h
            n_bw = bw / w
            n_bh = bh / h

            label_lines.append(f"{cls_id} {n_cx:.6f} {n_cy:.6f} {n_bw:.6f} {n_bh:.6f}")
            normalized_boxes.append({
                "class_id": cls_id,
                "class_name": classes[cls_id] if cls_id < len(classes) else f"class_{cls_id}",
                "x1": x_min, "y1": y_min, "x2": x_max, "y2": y_max,
                "norm": [round(n_cx, 5), round(n_cy, 5), round(n_bw, 5), round(n_bh, 5)]
            })

        # 2. Processa Polígonos de Segmentação (YOLO-seg format: class_id x1 y1 x2 y2 ... xn yn)
        for poly in polygons:
            cls_id = int(poly.get("class_id", 0))
            if cls_id >= len(classes):
                cls_id = 0

            pts = poly.get("points", [])
            if len(pts) < 3:
                continue

            coords_norm = []
            pts_saved = []
            for p in pts:
                px = max(0.0, min(float(w), float(p["x"])))
                py = max(0.0, min(float(h), float(p["y"])))
                pts_saved.append({"x": px, "y": py})
                coords_norm.append(f"{px / w:.6f} {py / h:.6f}")

            label_lines.append(f"{cls_id} {' '.join(coords_norm)}")
            normalized_polygons.append({
                "class_id": cls_id,
                "class_name": classes[cls_id] if cls_id < len(classes) else f"class_{cls_id}",
                "points": pts_saved
            })

        with open(label_path, "w", encoding="utf-8") as f:
            f.write("\n".join(label_lines) + ("\n" if label_lines else ""))

        # Atualiza manifesto
        manifest = self._load_manifest()
        manifest[image_id] = {
            "id": image_id,
            "filename": img_filename,
            "label_file": label_filename,
            "width": w,
            "height": h,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_video": source_video,
            "frame_timestamp": frame_timestamp,
            "num_boxes": len(normalized_boxes),
            "num_polygons": len(normalized_polygons),
            "boxes": normalized_boxes,
            "polygons": normalized_polygons,
            "notes": notes
        }
        self._save_manifest(manifest)

        return {
            "status": "ok",
            "image_id": image_id,
            "filename": img_filename,
            "num_boxes": len(normalized_boxes),
            "num_polygons": len(normalized_polygons)
        }

    def load_annotation(self, image_id):
        """Carrega uma imagem e todas as suas anotações anteriores para edição direta no canvas."""
        manifest = self._load_manifest()
        if image_id not in manifest:
            return {"status": "error", "message": f"Anotação '{image_id}' não encontrada"}

        item = manifest[image_id]
        img_path = os.path.join(self.images_dir, item.get("filename", ""))
        if not os.path.exists(img_path):
            return {"status": "error", "message": "Arquivo de imagem não encontrado no disco"}

        img = cv2.imread(img_path)
        h, w = img.shape[:2]

        return {
            "status": "ok",
            "image_id": image_id,
            "filename": item.get("filename"),
            "image_url": f"/media/annotated/{item.get('filename')}",
            "width": w,
            "height": h,
            "source_video": item.get("source_video", "video"),
            "frame_timestamp": item.get("frame_timestamp", 0.0),
            "boxes": item.get("boxes", []),
            "polygons": item.get("polygons", [])
        }

    def list_annotations(self):
        """Lista todas as anotações do dataset com resumo."""
        manifest = self._load_manifest()
        items = list(manifest.values())
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {
            "total_images": len(items),
            "total_boxes": sum(i.get("num_boxes", 0) for i in items),
            "total_polygons": sum(i.get("num_polygons", 0) for i in items),
            "classes": self.get_classes(),
            "items": items
        }

    def delete_annotation(self, image_id):
        """Exclui uma imagem e sua respectiva anotação do dataset."""
        manifest = self._load_manifest()
        if image_id not in manifest:
            return {"status": "error", "message": "ID não encontrado"}

        info = manifest[image_id]
        img_path = os.path.join(self.images_dir, info.get("filename", ""))
        lbl_path = os.path.join(self.labels_dir, info.get("label_file", ""))

        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass

        if os.path.exists(lbl_path):
            try: os.remove(lbl_path)
            except Exception: pass

        del manifest[image_id]
        self._save_manifest(manifest)
        return {"status": "ok", "deleted_id": image_id}

    def import_dataset_zip(self, zip_path_or_file):
        """
        Importa um arquivo ZIP contendo um dataset YOLO existente para continuar a anotação.
        Reconstrói o manifesto e atualiza as classes no data.yaml.
        """
        extract_dir = os.path.join(self.dataset_dir, f"import_temp_{int(time.time())}")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path_or_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Busca classes em classes.txt ou data.yaml
            imported_classes = None
            for root, _, files in os.walk(extract_dir):
                if "classes.txt" in files:
                    with open(os.path.join(root, "classes.txt"), "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f.readlines() if l.strip()]
                        if lines: imported_classes = lines
                elif "data.yaml" in files and not imported_classes:
                    try:
                        with open(os.path.join(root, "data.yaml"), "r", encoding="utf-8") as f:
                            content = f.read()
                            # Parse simples de names:
                            if "names:" in content:
                                lines = content.split("names:")[1].splitlines()
                                cls_names = []
                                for l in lines:
                                    if ":" in l:
                                        val = l.split(":", 1)[1].strip().strip("'\"")
                                        if val: cls_names.append(val)
                                if cls_names: imported_classes = cls_names
                    except Exception:
                        pass

            if imported_classes:
                self.set_classes(imported_classes)

            classes = self.get_classes()
            manifest = self._load_manifest()
            imported_count = 0

            # Procura imagens e respectivos labels
            for root, _, files in os.walk(extract_dir):
                for f in files:
                    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        img_src = os.path.join(root, f)
                        base_name = os.path.splitext(f)[0]
                        img_id = str(uuid.uuid4())[:8]
                        new_img_name = f"imported_{img_id}_{f}"
                        new_lbl_name = f"imported_{img_id}_{base_name}.txt"

                        # Copia imagem
                        dest_img = os.path.join(self.images_dir, new_img_name)
                        shutil.copy2(img_src, dest_img)

                        img_bgr = cv2.imread(dest_img)
                        h, w = img_bgr.shape[:2] if img_bgr is not None else (720, 1280)

                        # Busca label correspondente
                        boxes = []
                        polygons = []
                        dest_lbl = os.path.join(self.labels_dir, new_lbl_name)

                        # Tenta achar arquivo .txt de label no zip
                        found_lbl = None
                        for l_root, _, l_files in os.walk(extract_dir):
                            if f"{base_name}.txt" in l_files:
                                found_lbl = os.path.join(l_root, f"{base_name}.txt")
                                break

                        if found_lbl and os.path.exists(found_lbl):
                            shutil.copy2(found_lbl, dest_lbl)
                            with open(dest_lbl, "r", encoding="utf-8") as l_fp:
                                for line in l_fp:
                                    parts = line.strip().split()
                                    if not parts: continue
                                    cls_id = int(parts[0])
                                    floats = [float(x) for x in parts[1:]]

                                    if len(floats) == 4:
                                        # BBox [cx, cy, bw, bh]
                                        cx, cy, bw, bh = floats
                                        x1 = (cx - bw/2.0) * w
                                        y1 = (cy - bh/2.0) * h
                                        x2 = (cx + bw/2.0) * w
                                        y2 = (cy + bh/2.0) * h
                                        boxes.append({
                                            "class_id": cls_id,
                                            "class_name": classes[cls_id] if cls_id < len(classes) else f"class_{cls_id}",
                                            "x1": max(0, x1), "y1": max(0, y1),
                                            "x2": min(w, x2), "y2": min(h, y2),
                                            "norm": [cx, cy, bw, bh]
                                        })
                                    elif len(floats) >= 6 and len(floats) % 2 == 0:
                                        # Polígono [x1, y1, x2, y2, ...]
                                        pts = []
                                        for i in range(0, len(floats), 2):
                                            pts.append({"x": floats[i] * w, "y": floats[i+1] * h})
                                        polygons.append({
                                            "class_id": cls_id,
                                            "class_name": classes[cls_id] if cls_id < len(classes) else f"class_{cls_id}",
                                            "points": pts
                                        })
                        else:
                            # Cria label vazio
                            with open(dest_lbl, "w", encoding="utf-8") as l_fp:
                                l_fp.write("")

                        manifest[img_id] = {
                            "id": img_id,
                            "filename": new_img_name,
                            "label_file": new_lbl_name,
                            "width": w,
                            "height": h,
                            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "source_video": "imported_dataset",
                            "frame_timestamp": 0.0,
                            "num_boxes": len(boxes),
                            "num_polygons": len(polygons),
                            "boxes": boxes,
                            "polygons": polygons,
                            "notes": "Importado via ZIP"
                        }
                        imported_count += 1

            self._save_manifest(manifest)
            return {
                "status": "ok",
                "imported_images": imported_count,
                "classes": classes
            }, None

        except Exception as e:
            return None, f"Erro ao importar dataset: {str(e)}"
        finally:
            if os.path.exists(extract_dir):
                try: shutil.rmtree(extract_dir)
                except Exception: pass

    def export_dataset_zip(self, split_ratio=0.8):
        """Empacota o dataset no padrão YOLO (train / val) e gera um arquivo .zip para download."""
        manifest = self._load_manifest()
        items = list(manifest.values())
        if not items:
            return None, "Dataset está vazio. Adicione pelo menos uma imagem anotada."

        export_id = f"dataset_yolo_{time.strftime('%Y%m%d_%H%M%S')}"
        temp_dir = os.path.join(self.exports_dir, export_id)
        zip_path = os.path.join(self.exports_dir, f"{export_id}.zip")

        train_img_dir = os.path.join(temp_dir, "images", "train")
        val_img_dir = os.path.join(temp_dir, "images", "val")
        train_lbl_dir = os.path.join(temp_dir, "labels", "train")
        val_lbl_dir = os.path.join(temp_dir, "labels", "val")

        for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
            os.makedirs(d, exist_ok=True)

        np.random.seed(42)
        indices = np.random.permutation(len(items))
        split_idx = int(len(items) * split_ratio)
        if split_idx == len(items) and len(items) > 1:
            split_idx = len(items) - 1

        for pos, idx in enumerate(indices):
            item = items[idx]
            is_train = pos < split_idx

            dest_img_dir = train_img_dir if is_train else val_img_dir
            dest_lbl_dir = train_lbl_dir if is_train else val_lbl_dir

            src_img = os.path.join(self.images_dir, item["filename"])
            src_lbl = os.path.join(self.labels_dir, item["label_file"])

            if os.path.exists(src_img):
                shutil.copy2(src_img, os.path.join(dest_img_dir, item["filename"]))
            if os.path.exists(src_lbl):
                shutil.copy2(src_lbl, os.path.join(dest_lbl_dir, item["label_file"]))

        classes = self.get_classes()
        yaml_content = f"""# Dataset YOLO para Detecção e Segmentação Naval - Exportado do Painel
path: ./
train: images/train
val: images/val

nc: {len(classes)}
names:
"""
        for c_idx, c_name in enumerate(classes):
            yaml_content += f"  {c_idx}: {c_name}\n"

        with open(os.path.join(temp_dir, "data.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        with open(os.path.join(temp_dir, "classes.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(classes) + "\n")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)

        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

        return zip_path, None

# -*- coding: utf-8 -*-
"""
Motor de Data Augmentation para Datasets de Visão Computacional (YOLO BBox & Seg).
Gera variações realistas preservando a consistência geométrica das caixas e polígonos de segmentação.
"""

import os
import random
import cv2
import numpy as np

class DatasetAugmentationEngine:
    """
    Executa transformações geométricas e fotométricas em imagens e recalculando
    com precisão matemática todas as bounding boxes e vértices de polígonos.
    """

    @staticmethod
    def flip_horizontal(img: np.ndarray, boxes: list, polygons: list):
        """Espelhamento horizontal da imagem e ajuste das coordenadas X."""
        h, w = img.shape[:2]
        flipped_img = cv2.flip(img, 1)

        new_boxes = []
        for b in boxes:
            x1, y1, x2, y2 = b.get("x1", 0), b.get("y1", 0), b.get("x2", 0), b.get("y2", 0)
            nb = dict(b)
            nb["x1"] = max(0, w - x2)
            nb["x2"] = min(w, w - x1)
            nb["y1"] = y1
            nb["y2"] = y2
            new_boxes.append(nb)

        new_polygons = []
        for poly in polygons:
            npoly = dict(poly)
            npoly["points"] = [{"x": max(0, w - pt["x"]), "y": pt["y"]} for pt in poly.get("points", [])]
            new_polygons.append(npoly)

        return flipped_img, new_boxes, new_polygons, "Flip Horizontal"

    @staticmethod
    def adjust_brightness_contrast(img: np.ndarray, boxes: list, polygons: list, alpha: float = 1.25, beta: int = 15):
        """Ajuste de brilho e contraste (fotométrico - não altera coordenadas)."""
        adj_img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        return adj_img, [dict(b) for b in boxes], [dict(p) for p in polygons], f"Brilho/Contraste (α={alpha:.2f}, β={beta})"

    @staticmethod
    def add_gaussian_noise(img: np.ndarray, boxes: list, polygons: list, sigma: float = 18.0):
        """Adiciona ruído gaussiano (simulação de baixa luminosidade e granulação de sensor)."""
        noise = np.random.normal(0, sigma, img.shape).astype(np.float32)
        noisy_img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        return noisy_img, [dict(b) for b in boxes], [dict(p) for p in polygons], "Ruído de Sensor Gaussiano"

    @staticmethod
    def add_motion_blur(img: np.ndarray, boxes: list, polygons: list, kernel_size: int = 5):
        """Simula leve desfoque de movimento da câmera ou embarcação."""
        kernel = np.zeros((kernel_size, kernel_size))
        kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)
        kernel = kernel / kernel_size
        blurred = cv2.filter2D(img, -1, kernel)
        return blurred, [dict(b) for b in boxes], [dict(p) for p in polygons], "Desfoque de Movimento"

    @staticmethod
    def simulate_fog_weather(img: np.ndarray, boxes: list, polygons: list, intensity: float = 0.35):
        """Simula condições climáticas de névoa / maresia / neblina marítima."""
        h, w = img.shape[:2]
        fog_layer = np.full((h, w, 3), 210, dtype=np.uint8)
        foggy = cv2.addWeighted(img, 1.0 - intensity, fog_layer, intensity, 0)
        return foggy, [dict(b) for b in boxes], [dict(p) for p in polygons], "Simulação de Névoa / Neblina"

    @staticmethod
    def rotate_slight(img: np.ndarray, boxes: list, polygons: list, angle_degrees: float = 8.0):
        """Rotação suave em torno do centro com recálculo trigonométrico de vértices e caixas."""
        h, w = img.shape[:2]
        center = (w / 2.0, h / 2.0)
        M = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)
        rotated_img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        def transform_pt(px, py):
            pt = np.array([px, py, 1.0])
            new_pt = M.dot(pt)
            return float(np.clip(new_pt[0], 0, w)), float(np.clip(new_pt[1], 0, h))

        new_boxes = []
        for b in boxes:
            x1, y1, x2, y2 = b.get("x1", 0), b.get("y1", 0), b.get("x2", 0), b.get("y2", 0)
            corners = [
                transform_pt(x1, y1),
                transform_pt(x2, y1),
                transform_pt(x2, y2),
                transform_pt(x1, y2)
            ]
            xs = [c[0] for c in corners]
            ys = [c[1] for c in corners]
            nb = dict(b)
            nb["x1"] = max(0, min(xs))
            nb["x2"] = min(w, max(xs))
            nb["y1"] = max(0, min(ys))
            nb["y2"] = min(h, max(ys))
            new_boxes.append(nb)

        new_polygons = []
        for poly in polygons:
            npoly = dict(poly)
            npoly["points"] = [{"x": transform_pt(p["x"], p["y"])[0], "y": transform_pt(p["x"], p["y"])[1]} for p in poly.get("points", [])]
            new_polygons.append(npoly)

        return rotated_img, new_boxes, new_polygons, f"Rotação ({angle_degrees:+.1f}°)"

    @classmethod
    def apply_horizontal_flip(cls, img: np.ndarray, boxes: list, polygons: list):
        """Helper para retorno direto de (img, boxes, polygons)."""
        res_img, b, p, _ = cls.flip_horizontal(img, boxes, polygons)
        return res_img, b, p

    @classmethod
    def apply_rotation(cls, img: np.ndarray, boxes: list, polygons: list, angle: float = 8.0):
        """Helper para retorno direto de (img, boxes, polygons)."""
        res_img, b, p, _ = cls.rotate_slight(img, boxes, polygons, angle_degrees=angle)
        return res_img, b, p

    @classmethod
    def generate_augmentations_for_frame(cls, img_bgr: np.ndarray, boxes: list, polygons: list, options: dict = None) -> list:
        """
        Gera uma lista de variações aumentadas a partir de um frame anotado.
        
        Args:
            img_bgr: Imagem original.
            boxes: Lista de caixas anotadas.
            polygons: Lista de polígonos anotados.
            options: Dicionário com flags e parâmetros (flip, brightness, noise, blur, fog, rotate, count).
            
        Returns:
            Lista de dicionários com { 'image_bgr', 'boxes', 'polygons', 'name', 'tag' }.
        """
        options = options or {}
        results = []

        # 1. Flip Horizontal
        if options.get("flip_h", True):
            img_aug, b_aug, p_aug, name = cls.flip_horizontal(img_bgr, boxes, polygons)
            results.append({"image_bgr": img_aug, "boxes": b_aug, "polygons": p_aug, "name": name, "tag": "flip_h"})

        # 2. Brilho Elevado (Dia Ensolarado)
        if options.get("bright_high", True):
            img_aug, b_aug, p_aug, name = cls.adjust_brightness_contrast(img_bgr, boxes, polygons, alpha=1.2, beta=20)
            results.append({"image_bgr": img_aug, "boxes": b_aug, "polygons": p_aug, "name": name, "tag": "bright_high"})

        # 3. Baixa Luz / Sombra
        if options.get("bright_low", True):
            img_aug, b_aug, p_aug, name = cls.adjust_brightness_contrast(img_bgr, boxes, polygons, alpha=0.8, beta=-15)
            results.append({"image_bgr": img_aug, "boxes": b_aug, "polygons": p_aug, "name": name, "tag": "bright_low"})

        # 4. Ruído de Sensor
        if options.get("noise", True):
            img_aug, b_aug, p_aug, name = cls.add_gaussian_noise(img_bgr, boxes, polygons, sigma=16.0)
            results.append({"image_bgr": img_aug, "boxes": b_aug, "polygons": p_aug, "name": name, "tag": "noise"})

        # 5. Rotação Leve Positiva
        if options.get("rotate_pos", True):
            img_aug, b_aug, p_aug, name = cls.rotate_slight(img_bgr, boxes, polygons, angle_degrees=7.5)
            results.append({"image_bgr": img_aug, "boxes": b_aug, "polygons": p_aug, "name": name, "tag": "rot_pos"})

        # 6. Rotação Leve Negativa
        if options.get("rotate_neg", True):
            img_aug, b_aug, p_aug, name = cls.rotate_slight(img_bgr, boxes, polygons, angle_degrees=-7.5)
            results.append({"image_bgr": img_aug, "boxes": b_aug, "polygons": p_aug, "name": name, "tag": "rot_neg"})

        # 7. Neblina / Clima Adverso
        if options.get("fog", False):
            img_aug, b_aug, p_aug, name = cls.simulate_fog_weather(img_bgr, boxes, polygons, intensity=0.30)
            results.append({"image_bgr": img_aug, "boxes": b_aug, "polygons": p_aug, "name": name, "tag": "fog"})

        return results

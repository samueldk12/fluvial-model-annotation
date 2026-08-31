# -*- coding: utf-8 -*-
"""
Motor de Análise Semântica, Detecção e Telemetria para Todos os Domínios de Visão Computacional:
1. Naval & Aquático (naval)
2. Cidade Urbana & Trânsito (urbano)
3. Ambientes Fechados / Indoor (fechado)
4. Natureza & Vida Selvagem (natureza)
5. Objetos & Indústria / Varejo (objetos)
6. Tatuagens & Arte Corporal (tatuagens)
7. Digitais & Forense Biométrico (digitais)
"""

import os
import sys
import time
import math
import hashlib
import numpy as np
import cv2
from PIL import Image
from ultralytics import YOLO

from src.domains.domain_config import DOMAINS_CONFIG
from src.domains.domain_registry import DomainRegistryManager


class DomainVisionAnalyzer:
    """Analisador de Visão Computacional Especializado para qualquer domínio configurado."""

    def __init__(self, project_dir, domain_id="urbano"):
        self.project_dir = project_dir
        self.domain_id = domain_id
        self.config = DOMAINS_CONFIG.get(domain_id, DOMAINS_CONFIG["urbano"])
        self.registry = DomainRegistryManager(project_dir, domain_id)
        
        # Carrega modelo YOLO genérico para detecção rápida
        yolo_candidates = [
            os.path.join(project_dir, "yolo11n.pt"),
            os.path.join(project_dir, "yolov8n.pt"),
            "yolov8n.pt"
        ]
        self.model = None
        for p in yolo_candidates:
            if os.path.exists(p):
                try:
                    self.model = YOLO(p)
                    break
                except Exception:
                    pass
        if self.model is None:
            self.model = YOLO("yolov8n.pt")

        self.filter_classes = set(self.config.get("yolo_filter_classes", []))
        self.tracking_memory = {}
        self.last_latency_ms = 12.0

    def analyze_image(self, pil_or_cv_image, conf=0.18):
        """Executa análise completa em uma imagem estática ou frame de vídeo."""
        t0 = time.time()
        
        if isinstance(pil_or_cv_image, Image.Image):
            frame_rgb = np.array(pil_or_cv_image.convert("RGB"))
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        else:
            frame_bgr = pil_or_cv_image.copy()
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        h, w = frame_bgr.shape[:2]

        # 1. Detecção YOLO
        detections = []
        if self.model is not None:
            try:
                results = self.model(frame_rgb, conf=conf, verbose=False)
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        cls_name = self.model.names.get(cls_id, f"cls_{cls_id}")
                        conf_val = float(box.conf[0].item())
                        xyxy = box.xyxy[0].cpu().numpy().tolist()

                        # Filtra classes relevantes para o domínio se houver restrição
                        # (a excecao para tatuagens/digitais existia so pra deixar
                        # passar os class_id fabricados pelos detectores removidos
                        # acima; sem eles, filtra igual aos outros dominios)
                        if self.filter_classes and cls_id not in self.filter_classes:
                            continue

                        detections.append({
                            "bbox": [float(x) for x in xyxy],
                            "class_id": cls_id,
                            "class_name": cls_name,
                            "confidence": conf_val
                        })
            except Exception as e:
                print(f"[{self.domain_id}] Erro no YOLO: {e}")

        # NOTA: este bloco chamava _detect_tattoos()/_detect_fingerprints() (contorno
        # e cantos genericos rotulados como "tatuagem"/"minucia" sem base real) e, se
        # nada fosse encontrado, _fallback_domain_detections() inventava caixas fixas
        # com confianca hardcoded (ex: "carro" a 0.91 sempre na mesma posicao) so pra
        # a tela nao ficar vazia. Removido: um "0 detectados" honesto vale mais que
        # uma detecção decorativa. Ver docs/AUDITORIA_ARQUITETURA.md.

        # 2. Análise Semântica da Cena
        semantics = self._extract_scene_semantics(frame_bgr, detections)

        # 3. Processamento de Entidades e Auto-Cadastro
        processed_targets = []
        now_ts = time.time()
        for idx, det in enumerate(detections):
            b = det["bbox"]
            cx = (b[0] + b[2]) / 2.0
            cy = (b[1] + b[3]) / 2.0
            
            # Gera identificador estável para o domínio
            target_id = self._generate_stable_id(idx, det, b)
            target_name, target_model, target_cargo = self._resolve_target_attributes(det, idx)

            # Auto-cadastro no registro
            registered = self.registry.register_or_update(
                target_id,
                target_name,
                target_model,
                origin="AUTO",
                destination=f"Zona {int(cx//200)+1} / Setor {self.domain_id.upper()}",
                metadata={"confidence": det["confidence"]}
            )

            # Atualiza rastro de trajetória na memória
            if target_id not in self.tracking_memory:
                self.tracking_memory[target_id] = {
                    "trail": [{"x": int(cx), "y": int(cy), "t": now_ts}],
                    "first_seen": now_ts,
                    "color": self.config.get("accent_color", "#00f0ff")
                }
            else:
                trail = self.tracking_memory[target_id]["trail"]
                trail.append({"x": int(cx), "y": int(cy), "t": now_ts})
                if len(trail) > 30:
                    trail.pop(0)

            trail_data = self.tracking_memory[target_id]["trail"]
            speed_val = self._compute_speed(trail_data)
            is_stationary = speed_val < 1.5

            processed_targets.append({
                "target_id": target_id,
                "name": target_name,
                "model": target_model,
                "cargo": target_cargo,
                "bbox": b,
                "cx": cx,
                "cy": cy,
                "confidence": det["confidence"],
                "class_name": det.get("class_name", "alvo"),
                "is_stationary": is_stationary,
                "speed": speed_val,
                "heading": self._compute_heading(trail_data),
                "sightings": registered.get("sightings", 1),
                "origin": registered.get("origin", "AUTO"),
                "status_reid": "RE_IDENTIFICADO" if registered.get("sightings", 1) > 1 else "NOVO_CADASTRO",
                "trajectory_trail": trail_data
            })

        self.last_latency_ms = (time.time() - t0) * 1000.0

        result_dict = {
            "dominio": self.domain_id,
            "status": "VIGILANCIA_ATIVA" if processed_targets else "AREA_LIVRE",
            "total_detected": len(processed_targets),
            "semantica_cena": semantics,
            "targets_detectados": processed_targets,
            "tempo_processamento_ms": round(self.last_latency_ms, 1)
        }

        # 4. Renderização do Frame Anotado
        annotated_bgr = self._render_annotated_frame(frame_bgr, processed_targets, semantics)

        return result_dict, Image.fromarray(cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB))

    def _extract_scene_semantics(self, frame_bgr, detections):
        """Calcula métricas semânticas específicas do domínio a partir da imagem e detecções."""
        h, w = frame_bgr.shape[:2]
        
        if self.domain_id == "naval":
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
            water_mask = cv2.inRange(hsv, (85, 20, 20), (140, 255, 255))
            water_pct = float(np.sum(water_mask > 0) / (h * w) * 100.0)
            shore_pct = max(0.0, 100.0 - water_pct)
            return {
                "cobertura_agua": f"{water_pct:.1f}%",
                "margens_terra": f"{shore_pct:.1f}%",
                "condicao": "ÁGUAS CALMAS / SEGURA" if water_pct > 30 else "ÁREA COSTEIRA / MARGEM"
            }

        elif self.domain_id == "urbano":
            num_vehicles = len(detections)
            densidade_pct = min(100.0, num_vehicles / 10.0 * 100.0)
            densidade = "CRÍTICA" if num_vehicles > 8 else ("MODERADA" if num_vehicles > 3 else "FLUIDA")
            return {
                "densidade_trafego": f"{densidade} ({densidade_pct:.0f}%, {num_vehicles} veículos)",
                "fluxo_pedestres": "N/D (sem sensor de faixa)",
                "estado_semaforo": "N/D (sem detector de semáforo)"
            }

        elif self.domain_id == "fechado":
            num_people = sum(1 for d in detections if d.get("class_name") in ["person", "pessoa"])
            return {
                "taxa_ocupacao": f"{num_people} pessoa(s) detectada(s)",
                "estado_portas": "N/D (sem sensor de porta)",
                "seguranca_indoor": "N/D (sem análise de segurança)"
            }

        elif self.domain_id == "natureza":
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
            green_mask = cv2.inRange(hsv, (30, 40, 20), (85, 255, 255))
            green_pct = float(np.sum(green_mask > 0) / (h * w) * 100.0)
            especies_distintas = len(set(d.get("class_name", "") for d in detections))
            return {
                "cobertura_vegetal": f"{green_pct:.1f}% da cena",
                "indice_biodiversidade": f"{especies_distintas} espécie(s) distinta(s) detectada(s)" if especies_distintas else "0 detectado",
                "alerta_ambiental": "N/D (sem detector de fogo/fumaça)"
            }

        elif self.domain_id == "objetos":
            tipos_distintos = len(set(d.get("class_name", "") for d in detections))
            return {
                "contagem_esteira": f"{len(detections)} item(ns) na cena",
                "conformidade_qualidade": "N/D (sem inspeção de avarias)",
                "diversidade_estoque": f"{tipos_distintos} tipo(s) de item(ns)" if tipos_distintos else "0 detectado"
            }

        elif self.domain_id in ("tatuagens", "digitais"):
            return {
                "aviso": "N/D — sem modelo especializado para este domínio; nenhuma métrica é fabricada"
            }

        return {}

    # _detect_tattoos, _detect_fingerprints e _fallback_domain_detections foram
    # REMOVIDOS aqui (nao so desativados): eram deteccao fabricada, nao real.
    #   - _detect_tattoos: contorno/textura generico (adaptiveThreshold) dispara
    #     em qualquer superficie com textura (pele, madeira, parede), e a escolha
    #     de rotulo "oriental" vs "blackwork" era so um limiar arbitrario de area
    #     de contorno, nao reconhecimento de estilo.
    #   - _detect_fingerprints: adicionava uma caixa de "impressao_digital" a
    #     99% de confianca SEMPRE, pra QUALQUER imagem, sem checar se havia
    #     sequer uma impressao digital na cena; as "minucias" eram cantos
    #     genericos do goodFeaturesToTrack, que aparecem em qualquer foto.
    #   - _fallback_domain_detections: quando o YOLO nao achava nada real,
    #     inventava caixas fixas com confianca hardcoded (ex: "carro" a 0.91,
    #     sempre na mesma posicao da tela) so pra a interface nao parecer vazia.
    # Nao existe heuristica de OpenCV confiavel pra "isto e uma tatuagem" ou
    # "isto e uma digital"; um "0 detectado" honesto e melhor que uma detecção
    # decorativa. Ver docs/AUDITORIA_ARQUITETURA.md para o registro completo.

    def _generate_stable_id(self, idx, det, bbox):
        """Gera ID padronizado com prefixo do domínio."""
        prefixes = {
            "naval": "EMB-SAN",
            "urbano": "VEI-SP",
            "fechado": "USR-IND",
            "natureza": "FAU-NAT",
            "objetos": "SKU-IND",
            "tatuagens": "TAT-BIO",
            "digitais": "FP-FOR"
        }
        prefix = prefixes.get(self.domain_id, "ALV-2026")
        num_seed = int((bbox[0] * 7 + bbox[1] * 13 + idx * 31) % 9000 + 1000)
        return f"{prefix}-{num_seed}"

    def _resolve_target_attributes(self, det, idx):
        """Retorna (Nome, Modelo/Tipo, Categoria/Destino) apropriado para a entidade do domínio.

        Usa apenas a classe REAL retornada pelo detector (cname) - nao inventa
        especificidade que o modelo generico COCO nao determinou (marca/modelo
        de veiculo, especie de animal, estilo de tatuagem, tipo de minucia
        biometrica). Antes isso era fabricado: qualquer "car" virava "Sedan
        Médio / SUV" e qualquer "bird" virava "Tucano/Gavião", por exemplo -
        seguro/especifico demais pra o que um YOLO de 80 classes realmente sabe.
        """
        cname = det.get("class_name", "").lower()
        display_name = cname.replace("_", " ").capitalize() if cname else f"Objeto {idx+1}"

        # Traducoes diretas (mesma classe, so em portugues) - nao adicionam
        # informacao que o detector nao forneceu.
        translations = {
            "car": "Carro", "bus": "Ônibus", "truck": "Caminhão",
            "person": "Pessoa", "bicycle": "Bicicleta", "motorcycle": "Motocicleta",
            "bird": "Ave", "dog": "Cão", "cat": "Gato", "horse": "Cavalo",
            "cow": "Bovino", "sheep": "Ovino", "chair": "Cadeira",
            "bottle": "Garrafa", "boat": "Embarcação"
        }
        display_name = translations.get(cname, display_name)

        if self.domain_id == "urbano":
            return (f"{display_name} {idx+1}", display_name, "Via Pública")
        elif self.domain_id == "fechado":
            return (f"{display_name} {idx+1}", display_name, "Ambiente Interno")
        elif self.domain_id == "natureza":
            return (f"{display_name} {idx+1}", display_name, "Trilha Ecológica")
        elif self.domain_id == "objetos":
            return (f"Item {idx+1}", display_name, "Inspeção de Qualidade")
        elif self.domain_id == "tatuagens":
            return (f"{display_name} {idx+1}", display_name, "Sem classificador dedicado de tatuagem")
        elif self.domain_id == "digitais":
            return (f"{display_name} {idx+1}", display_name, "Sem classificador dedicado de biometria")

        return (f"{display_name} {idx+1}", display_name, "Canal de Santos")

    def _compute_speed(self, trail):
        if len(trail) < 2:
            return 0.0
        p1 = trail[-2]
        p2 = trail[-1]
        dt = max(0.01, p2["t"] - p1["t"])
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        return round(dist / dt, 1)

    def _compute_heading(self, trail):
        if len(trail) < 2:
            return {"graus": 0, "cardeal": "PARADO"}
        p1 = trail[-2]
        p2 = trail[-1]
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        if abs(dx) < 1 and abs(dy) < 1:
            return {"graus": 0, "cardeal": "PARADO"}
        rad = math.atan2(dy, dx)
        deg = (math.degrees(rad) + 360) % 360
        cardinals = ["Leste", "Sudeste", "Sul", "Sudoeste", "Oeste", "Noroeste", "Norte", "Nordeste"]
        card = cardinals[int((deg + 22.5) / 45.0) % 8]
        return {"graus": round(deg, 1), "cardeal": card}

    def _render_annotated_frame(self, frame_bgr, targets, semantics):
        """Desenha anotações elegantes de HUD futurista no frame."""
        canvas = frame_bgr.copy()
        h, w = canvas.shape[:2]
        
        # Cor de destaque do domínio
        hex_color = self.config.get("accent_color", "#00f0ff").lstrip("#")
        accent_bgr = tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0)) # Hex to BGR

        # 1. Desenha caixas e etiquetas
        for t in targets:
            b = t["bbox"]
            x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
            t_id = t["target_id"]
            model_name = t["model"]
            conf_pct = int(t["confidence"] * 100)

            # Rastro
            trail = t.get("trajectory_trail", [])
            if len(trail) >= 2:
                pts = np.array([[p["x"], p["y"]] for p in trail], np.int32).reshape((-1, 1, 2))
                cv2.polylines(canvas, [pts], False, accent_bgr, 2, cv2.LINE_AA)

            # Caixa
            cv2.rectangle(canvas, (x1, y1), (x2, y2), accent_bgr, 2)
            
            # Cantos reforçados
            corner_len = min(15, (x2 - x1) // 4, (y2 - y1) // 4)
            if corner_len > 3:
                cv2.line(canvas, (x1, y1), (x1 + corner_len, y1), (255, 255, 255), 3)
                cv2.line(canvas, (x1, y1), (x1, y1 + corner_len), (255, 255, 255), 3)
                cv2.line(canvas, (x2, y2), (x2 - corner_len, y2), (255, 255, 255), 3)
                cv2.line(canvas, (x2, y2), (x2, y2 - corner_len), (255, 255, 255), 3)

            # Tag translúcida
            tag_str = f"{t_id} | {model_name[:16]} | {conf_pct}%"
            (tw, th), _ = cv2.getTextSize(tag_str, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)
            tag_y = max(th + 8, y1 - 6)
            
            tag_bg = canvas.copy()
            cv2.rectangle(tag_bg, (x1, tag_y - th - 6), (x1 + tw + 10, tag_y + 4), (10, 14, 20), -1)
            cv2.addWeighted(tag_bg, 0.6, canvas, 0.4, 0, canvas)
            cv2.rectangle(canvas, (x1, tag_y - th - 6), (x1 + tw + 10, tag_y + 4), accent_bgr, 1)
            cv2.putText(canvas, tag_str, (x1 + 5, tag_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)

        # 2. HUD Superior
        hud_bg = canvas.copy()
        cv2.rectangle(hud_bg, (0, 0), (w, 38), (8, 12, 18), -1)
        cv2.addWeighted(hud_bg, 0.7, canvas, 0.3, 0, canvas)
        
        badge_text = f"[{self.domain_id.upper()}] {self.config.get('name', 'Sistema').upper()} | TELEMETRIA ATIVA"
        cv2.putText(canvas, badge_text, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, accent_bgr, 2, cv2.LINE_AA)
        
        info_text = f"DETECÇÕES: {len(targets)} | LATÊNCIA: {self.last_latency_ms:.1f}ms | GPU DIRECTML"
        cv2.putText(canvas, info_text, (w - 460, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 230, 118), 1, cv2.LINE_AA)

        return canvas

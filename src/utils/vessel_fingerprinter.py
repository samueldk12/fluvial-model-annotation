"""
Extrator Multimodal de Características Únicas e Identificação de Embarcações (Naval Vessel Fingerprinter).
Combina:
1. Leitura de Textos e Inscrições no Casco / IMO / Nomes (OCR).
2. Paleta Cromática Estruturada (Casco, Borda-Livre, Superestrutura).
3. Assinatura Geométrica e Silhueta (Aspect Ratio, Posição do Passadiço, Guindastes).
4. Assinatura Latente de 768D (Vision Transformer).
"""

import cv2
import numpy as np
import math
import re
from PIL import Image

from src.ocr.imo_validator import IMOValidator
from src.ocr.hull_rectifier import HullPerspectiveRectifier


class VesselFingerprintExtractor:
    def __init__(self):
        self.ocr_reader = None
        self._init_ocr()

    def _init_ocr(self):
        try:
            import easyocr
            # Inicializar leitor leve para inglês e português
            self.ocr_reader = easyocr.Reader(['en', 'pt'], gpu=False, verbose=False)
            print("[OCR] Leitor EasyOCR inicializado para identificação de nomes e números IMO.")
        except Exception as e:
            print(f"[OCR] EasyOCR inicialização em segundo plano / fallback ativo: {e}")
            self.ocr_reader = None

        self.rectifier = HullPerspectiveRectifier()
        self.validator = IMOValidator()

    def extract_hull_text(self, vessel_crop_bgr, enable_ocr=True):
        if not enable_ocr:
            return {"raw_texts": [], "detected_name": None, "imo_number": None, "ocr_attempted": False}
        if vessel_crop_bgr is None or vessel_crop_bgr.size == 0:
            return {"raw_texts": [], "detected_name": None, "imo_number": None, "ocr_attempted": True}

        h, w = vessel_crop_bgr.shape[:2]
        if h < 20 or w < 20:
            return {"raw_texts": [], "detected_name": None, "imo_number": None, "ocr_attempted": True}

        enhanced_crop = self.rectifier.rectify_and_enhance(vessel_crop_bgr, upscale_factor=2.0)
        detected_texts = []

        if self.ocr_reader is not None:
            try:
                results = self.ocr_reader.readtext(enhanced_crop)
                for res in results:
                    text_str = res[1].strip()
                    conf = float(res[2])
                    if conf > 0.25 and len(text_str) >= 3:
                        detected_texts.append(text_str)
            except Exception:
                pass

        imo_num = None
        cleaned_name = None

        for t in detected_texts:
            t_upper = t.upper()
            valid_imos = self.validator.extract_and_validate_from_text(t_upper)
            if valid_imos and not imo_num:
                imo_num = valid_imos[0]
            elif re.search(r'^[A-Z\s]{4,20}$', t_upper) and not cleaned_name:
                cleaned_name = t_upper

        return {
            "raw_texts": detected_texts,
            "detected_name": cleaned_name,
            "imo_number": imo_num,
            "ocr_attempted": True
        }

    def extract_color_palette(self, vessel_crop_bgr):
        """
        Extrai a paleta de cores dominante do Casco (metade inferior) e
        Superestrutura (metade superior) da embarcação.
        """
        if vessel_crop_bgr is None or vessel_crop_bgr.size == 0:
            return {
                "cor_casco_predominante": "Azul Marinho / Escuro",
                "cor_superestrutura": "Branco Naval",
                "hex_casco": "#1A2530",
                "hex_superestrutura": "#EAEAEA"
            }

        h, w = vessel_crop_bgr.shape[:2]
        
        # Segmentar Casco (inferior) e Passadiço/Superestrutura (superior)
        upper_crop = vessel_crop_bgr[:int(h * 0.45), :]
        lower_crop = vessel_crop_bgr[int(h * 0.45):, :]

        def get_dominant_color_name(crop):
            if crop.size == 0:
                return "Cinzento", "#808080"
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            h_ch, s_ch, v_ch = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
            s_mean = float(np.mean(s_ch))
            v_mean = float(np.mean(v_ch))
            b_mean, g_mean, r_mean = np.mean(crop[:, :, 0]), np.mean(crop[:, :, 1]), np.mean(crop[:, :, 2])
            hex_code = f"#{int(r_mean):02x}{int(g_mean):02x}{int(b_mean):02x}"

            if v_mean < 45:
                return "Preto / Escuro Grafite", hex_code
            if v_mean > 190 and s_mean < 40:
                return "Branco Naval", hex_code
            if s_mean < 35:
                return "Cinza Marítimo", hex_code

            # Matiz (Hue) e uma grandeza CIRCULAR: 0 e 179 sao vizinhos no
            # circulo de cores, nao extremos opostos. Um casco vermelho real
            # tem pixels perto de AMBAS as pontas (vermelho vivo ~hue 2-5 e
            # vermelho escuro/bordo ~hue 175-179, por sombra/iluminacao) - a
            # MEDIA aritmetica desses pixels cai no MEIO do circulo (~90),
            # que caia incorretamente no balde "Azul/Ciano". Testado: casco
            # sintetico vermelho (hues 3 e 176) dava h_mean=89.5, classificado
            # como azul. Trocado para a MODA (pico do histograma) dos pixels
            # cromaticos (saturacao > 40, ignorando cinza/branco/preto que
            # tem matiz sem sentido) - nao sofre de wraparound e e mais
            # robusta a contaminacao por agua de fundo no recorte.
            chromatic_mask = s_ch > 40
            if np.count_nonzero(chromatic_mask) < 10:
                h_dominant = float(np.median(h_ch))
            else:
                hist = np.bincount(h_ch[chromatic_mask].astype(np.uint8), minlength=180)
                h_dominant = float(np.argmax(hist))

            if h_dominant < 10 or h_dominant > 170:
                return "Vermelho Óxido / Anti-Incrustante", hex_code
            if 10 <= h_dominant <= 30:
                return "Laranja / Amarelo Segurança", hex_code
            if 31 <= h_dominant <= 85:
                return "Verde Náutico", hex_code
            if 86 <= h_dominant <= 130:
                return "Azul Marinho / Ciano", hex_code
            return "Azul Petróleo", hex_code

        hull_color, hull_hex = get_dominant_color_name(lower_crop)
        super_color, super_hex = get_dominant_color_name(upper_crop)

        return {
            "cor_casco_predominante": hull_color,
            "cor_superestrutura": super_color,
            "hex_casco": hull_hex,
            "hex_superestrutura": super_hex
        }

    def extract_geometric_silhouette(self, vessel_crop_bgr, bbox):
        """
        Analisa a silhueta, proporção comprimento/altura e posicionamento da cabine/passadiço.
        """
        x1, y1, x2, y2 = bbox
        bw = x2 - x1
        bh = max(1, y2 - y1)
        aspect_ratio = round(bw / float(bh), 2)

        # Porte estimado
        if bw > 300 or aspect_ratio > 4.5:
            porte = "Grande Porte (Mercante / Graneleiro / Porta-Contêiner)"
        elif bw > 140 or aspect_ratio > 2.8:
            porte = "Médio Porte (Balsa / Rebocador Oceânico / Pesqueiro)"
        else:
            porte = "Pequeno Porte (Lancha de Praticagem / Apoio Portuário)"

        # Posição da Superestrutura (analisar centro de massa da metade superior)
        h, w = vessel_crop_bgr.shape[:2] if (vessel_crop_bgr is not None and vessel_crop_bgr.size > 0) else (100, 200)
        upper = vessel_crop_bgr[:int(h * 0.45), :] if (vessel_crop_bgr is not None and vessel_crop_bgr.size > 0) else None
        
        bridge_position = "Popa (Aft) - Estilo Graneleiro/Cargueiro Moderno"
        if upper is not None and upper.size > 0:
            gray = cv2.cvtColor(upper, cv2.COLOR_BGR2GRAY)
            bright_cols = np.mean(gray, axis=0)
            if len(bright_cols) > 10:
                cx_bright = np.argmax(bright_cols)
                if cx_bright < w * 0.35:
                    bridge_position = "Proa (Forward) - Estilo Supply / Apoio Offshore"
                elif cx_bright > w * 0.65:
                    bridge_position = "Popa (Aft) - Estilo Mercante / Petroleiro"
                else:
                    bridge_position = "Meio-Navio (Midship) - Estilo Passageiro / Clássico"

        return {
            "proporcao_comprimento_altura": f"{aspect_ratio}:1",
            "porte_estrutural": porte,
            "posicao_passadico_superestrutura": bridge_position
        }

    def generate_unique_fingerprint(self, vessel_crop_bgr, bbox, vit_embedding_768d=None, enable_ocr=True, reid_embedding=None):
        """
        Consolida todas as características em uma assinatura digital única da embarcação.
        """
        ocr_info = self.extract_hull_text(vessel_crop_bgr, enable_ocr=enable_ocr)
        color_info = self.extract_color_palette(vessel_crop_bgr)
        geom_info = self.extract_geometric_silhouette(vessel_crop_bgr, bbox)

        # Determinar Nome Sugerido
        if ocr_info["detected_name"]:
            suggested_name = f"Navio {ocr_info['detected_name']}"
        elif ocr_info["imo_number"]:
            suggested_name = f"Embarcação {ocr_info['imo_number']}"
        else:
            suggested_name = f"Vessel-{color_info['cor_casco_predominante'].split()[0]}-{geom_info['porte_estrutural'].split()[0]}"

        fingerprint = {
            "nome_identificado_ou_sugerido": suggested_name,
            "numero_imo": ocr_info["imo_number"] or "IMO Não Localizado no Casco",
            "textos_lidos_no_casco": ocr_info["raw_texts"] if ocr_info["raw_texts"] else ["Sem inscrições legíveis"],
            "ocr_attempted": ocr_info.get("ocr_attempted", False),
            "texto_extraido": {
                "imo_number": ocr_info["imo_number"],
                "detected_name": ocr_info["detected_name"]
            },
            "caracteristicas_visuais": {
                "cor_casco": color_info["cor_casco_predominante"],
                "hex_casco": color_info["hex_casco"],
                "cor_superestrutura": color_info["cor_superestrutura"],
                "hex_superestrutura": color_info["hex_superestrutura"],
                "proporcao_L_H": geom_info["proporcao_comprimento_altura"],
                "porte": geom_info["porte_estrutural"],
                "posicao_passadico": geom_info["posicao_passadico_superestrutura"]
            }
        }
        if reid_embedding is not None:
            fingerprint["reid_embedding"] = reid_embedding
        return fingerprint

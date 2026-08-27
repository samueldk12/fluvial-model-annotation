"""
Interface Gráfica Interativa de Visão Computacional, Detecção, Anotação e Re-ID.
Suporta modelos de IA acopláveis, reprodução e pausa de vídeo/câmera, edição de anotações
e correção de predições da IA para active learning.
"""

import os
import sys
import time
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np

# Configurar UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Adicionar raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.pipeline.vessel_semantic_analyzer import VesselSemanticAnalyzer
from src.pipeline.pluggable_pipeline import PluggableVisionPipeline
from src.annotation.dataset_manager import DatasetAnnotationManager


class VesselPerceptionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Visão Naval — Percepção, IA Acoplada & Estúdio de Anotação")
        self.root.geometry("1440x900")
        self.root.configure(bg="#080e14")

        self.analyzer = VesselSemanticAnalyzer()
        self.pipeline = PluggableVisionPipeline(project_root, vit_analyzer=self.analyzer)
        self.dataset_manager = DatasetAnnotationManager(project_root, "naval")

        # Estado da Imagem / Vídeo
        self.current_image = None
        self.current_raw_frame = None
        self.current_image_path = None
        self.latest_result = None

        # Estado de Vídeo
        self.cap = None
        self.is_video_playing = False
        self.video_fps = 30.0
        self.video_total_frames = 0
        self.video_current_frame = 0

        # Estado de Anotação Interativa
        self.boxes = []
        self.selected_box_idx = -1
        self.drag_mode = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.initial_box = None
        self.canvas_scale = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0

        self.classes = self.dataset_manager.get_classes()
        self.class_colors = ["#00f0ff", "#1890ff", "#fa8c16", "#52c41a", "#722ed1", "#eb2f96", "#fadb14", "#8c8c8c"]

        self.setup_ui()
        self.refresh_port_table()
        self.load_models_catalog()

    def setup_ui(self):
        # HEADER
        header_frame = tk.Frame(self.root, bg="#0e1a26", height=54, bd=1, relief="ridge")
        header_frame.pack(fill="x", side="top", padx=8, pady=4)

        title_lbl = tk.Label(
            header_frame,
            text="SISTEMA DE SEMÂNTICA NAVAL & ANOTAÇÃO ASSISTIDA POR IA (HUMAN-IN-THE-LOOP)",
            font=("Segoe UI", 11, "bold"),
            bg="#0e1a26",
            fg="#ffffff"
        )
        title_lbl.pack(side="left", padx=12, pady=6)

        self.lbl_hw = tk.Label(
            header_frame,
            text=f"● {self.analyzer.dev_name} | PyTorch Modular",
            font=("Segoe UI", 9, "bold"),
            bg="#0e1a26",
            fg="#00e5ff"
        )
        self.lbl_hw.pack(side="right", padx=12, pady=6)

        main_frame = tk.Frame(self.root, bg="#080e14")
        main_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # ==========================================
        # COLUNA ESQUERDA (CONTROLES E MODELO DE IA)
        # ==========================================
        left_panel = tk.LabelFrame(main_frame, text=" Modelo de IA & Fontes ", bg="#101c28", fg="#00a8ff", font=("Segoe UI", 10, "bold"), width=340)
        left_panel.pack(side="left", fill="y", padx=4, pady=4)
        left_panel.pack_propagate(False)

        # 1. Seletor de Modelo de IA Atrelado
        model_box = tk.LabelFrame(left_panel, text=" 🤖 Modelo de IA Atrelado ", bg="#0a131c", fg="#a06cf8", font=("Segoe UI", 9, "bold"))
        model_box.pack(fill="x", padx=8, pady=6)

        self.cb_models = ttk.Combobox(model_box, state="readonly", font=("Segoe UI", 9))
        self.cb_models.pack(fill="x", padx=8, pady=6)
        self.cb_models.bind("<<ComboboxSelected>>", self.on_model_changed)

        self.lbl_model_desc = tk.Label(model_box, text="Carregando modelo...", bg="#0a131c", fg="#c0d2e5", font=("Segoe UI", 8), wraplength=300, justify="left")
        self.lbl_model_desc.pack(fill="x", padx=8, pady=2)

        # 2. Fontes de Vídeo e Imagem
        src_box = tk.LabelFrame(left_panel, text=" 📁 Fontes de Mídia ", bg="#0a131c", fg="#00e5ff", font=("Segoe UI", 9, "bold"))
        src_box.pack(fill="x", padx=8, pady=6)

        btn_img = tk.Button(src_box, text="📁 Carregar Imagem", font=("Segoe UI", 9, "bold"), bg="#18314d", fg="#ffffff", relief="flat", command=self.load_image_dialog)
        btn_img.pack(fill="x", padx=8, pady=3)

        btn_vid = tk.Button(src_box, text="🎬 Carregar Vídeo (.mp4)", font=("Segoe UI", 9, "bold"), bg="#163e2a", fg="#00e676", relief="flat", command=self.load_video_dialog)
        btn_vid.pack(fill="x", padx=8, pady=3)

        btn_sample = tk.Button(src_box, text="🌊 Amostra Real do Dataset", font=("Segoe UI", 9), bg="#1e2c3a", fg="#ffffff", relief="flat", command=self.load_dataset_sample)
        btn_sample.pack(fill="x", padx=8, pady=3)

        # 3. Ferramentas de Anotação & Correção da IA
        tool_box = tk.LabelFrame(left_panel, text=" ✏️ Anotação & Correção da IA ", bg="#0a131c", fg="#ff9100", font=("Segoe UI", 9, "bold"))
        tool_box.pack(fill="x", padx=8, pady=6)

        btn_ai_detect = tk.Button(tool_box, text="🤖 Executar IA no Frame (A)", font=("Segoe UI", 9, "bold"), bg="#531dab", fg="#ffffff", relief="flat", command=self.run_ai_on_current_frame)
        btn_ai_detect.pack(fill="x", padx=8, pady=3)

        btn_del_all = tk.Button(tool_box, text="🗑️ Deletar Todas Anotações", font=("Segoe UI", 9, "bold"), bg="#78111a", fg="#ff7875", relief="flat", command=self.delete_all_boxes)
        btn_del_all.pack(fill="x", padx=8, pady=3)

        btn_save = tk.Button(tool_box, text="💾 Salvar Frame no Dataset (Ctrl+S)", font=("Segoe UI", 9, "bold"), bg="#237804", fg="#ffffff", relief="flat", command=self.save_current_annotation)
        btn_save.pack(fill="x", padx=8, pady=3)

        # 4. Status
        self.lbl_status = tk.Label(left_panel, text="Status: Pronto", bg="#182838", fg="#ffffff", font=("Segoe UI", 9, "bold"), pady=6)
        self.lbl_status.pack(fill="x", padx=8, pady=8)

        # ==========================================
        # COLUNA CENTRAL (VISOR INTERATIVO & PLAYER)
        # ==========================================
        center_panel = tk.LabelFrame(main_frame, text=" Visor: Imagem com Predições & Edição Interativa ", bg="#101c28", fg="#00a8ff", font=("Segoe UI", 10, "bold"))
        center_panel.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        # Canvas Interativo
        self.canvas = tk.Canvas(center_panel, bg="#04080c", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_canvas_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_mouse_up)
        self.canvas.bind("<Configure>", lambda e: self.redraw_canvas())

        # Barra do Player de Vídeo
        player_bar = tk.Frame(center_panel, bg="#0e1a26", height=38)
        player_bar.pack(fill="x", side="bottom", padx=6, pady=4)

        self.btn_play = tk.Button(player_bar, text="▶ Play", font=("Segoe UI", 9, "bold"), bg="#1890ff", fg="#fff", relief="flat", width=8, command=self.toggle_play_video)
        self.btn_play.pack(side="left", padx=4, pady=4)

        btn_step_prev = tk.Button(player_bar, text="⏮ -1 Frame", font=("Segoe UI", 9), bg="#1f2f3f", fg="#fff", relief="flat", command=lambda: self.step_video_frame(-1))
        btn_step_prev.pack(side="left", padx=2, pady=4)

        btn_step_next = tk.Button(player_bar, text="⏭ +1 Frame", font=("Segoe UI", 9), bg="#1f2f3f", fg="#fff", relief="flat", command=lambda: self.step_video_frame(1))
        btn_step_next.pack(side="left", padx=2, pady=4)

        self.lbl_frame_info = tk.Label(player_bar, text="Frame: 0 / 0", bg="#0e1a26", fg="#c0d2e5", font=("Segoe UI", 9))
        self.lbl_frame_info.pack(side="right", padx=10, pady=4)

        # ==========================================
        # COLUNA DIREITA (CAMADAS / OBJETOS E REGISTRO)
        # ==========================================
        right_panel = tk.LabelFrame(main_frame, text=" Camadas do Frame & Registro ", bg="#101c28", fg="#00a8ff", font=("Segoe UI", 10, "bold"), width=380)
        right_panel.pack(side="right", fill="y", padx=4, pady=4)
        right_panel.pack_propagate(False)

        # Lista de Objetos / Caixas no Frame
        lbl_layers = tk.Label(right_panel, text="Objetos Detectados / Anotados:", bg="#101c28", fg="#c0d2e5", font=("Segoe UI", 9, "bold"), anchor="w")
        lbl_layers.pack(fill="x", padx=6, pady=2)

        self.list_boxes = tk.Listbox(right_panel, bg="#0a131c", fg="#00e5ff", font=("Segoe UI", 9), selectbackground="#1890ff", height=8)
        self.list_boxes.pack(fill="x", padx=6, pady=2)
        self.list_boxes.bind("<<ListboxSelect>>", self.on_box_selected_from_list)

        btn_del_sel = tk.Button(right_panel, text="✕ Excluir Objeto Selecionado", font=("Segoe UI", 8), bg="#3f1f1f", fg="#ff4d4f", relief="flat", command=self.delete_selected_box)
        btn_del_sel.pack(fill="x", padx=6, pady=2)

        # Tabela do Porto
        lbl_port = tk.Label(right_panel, text="Embarcações Cadastradas:", bg="#101c28", fg="#c0d2e5", font=("Segoe UI", 9, "bold"), anchor="w")
        lbl_port.pack(fill="x", padx=6, pady=4)

        columns = ("id", "name", "cargo", "origem")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", height=10)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Nome")
        self.tree.heading("cargo", text="Carga")
        self.tree.heading("origem", text="Origem")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("name", width=100, anchor="w")
        self.tree.column("cargo", width=90, anchor="w")
        self.tree.column("origem", width=55, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=6, pady=4)

        # Atalhos do Teclado
        self.root.bind("<space>", lambda e: self.toggle_play_video())
        self.root.bind("<a>", lambda e: self.run_ai_on_current_frame())
        self.root.bind("<Delete>", lambda e: self.delete_selected_box())
        self.root.bind("<Control-s>", lambda e: self.save_current_annotation())

    def load_models_catalog(self):
        catalog = self.pipeline.registry.get_catalog()
        model_names = [f"{m['name']} ({m['id']})" for m in catalog]
        self.cb_models["values"] = model_names
        if model_names:
            self.cb_models.current(0)
            self.on_model_changed()

    def on_model_changed(self, event=None):
        sel_idx = self.cb_models.current()
        catalog = self.pipeline.registry.get_catalog()
        if 0 <= sel_idx < len(catalog):
            m = catalog[sel_idx]
            self.pipeline.config["active_model_id"] = m["id"]
            self.lbl_model_desc.config(text=f"{m.get('description', '')} [Conf: {m.get('default_conf', 0.20):.2f}]")
            self.lbl_hw.config(text=f"● Modelo: {m['id']} | {m.get('framework', 'PyTorch')}")

    def load_image_dialog(self):
        self.stop_video()
        file_path = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp"), ("Todos os Arquivos", "*.*")]
        )
        if file_path:
            self.process_image_file(file_path)

    def load_video_dialog(self):
        self.stop_video()
        file_path = filedialog.askopenfilename(
            title="Selecionar Vídeo",
            filetypes=[("Vídeos", "*.mp4 *.avi *.webm *.mov"), ("Todos os Arquivos", "*.*")]
        )
        if file_path:
            self.open_video(file_path)

    def load_dataset_sample(self):
        self.stop_video()
        import glob, random
        samples = glob.glob(os.path.join(project_root, "data", "extracted_dataset", "**", "*.jpg"), recursive=True)
        if not samples:
            samples = glob.glob(os.path.join(project_root, "datasets", "**", "*.jpg"), recursive=True)
        if samples:
            chosen = random.choice(samples)
            self.process_image_file(chosen)
        else:
            messagebox.showinfo("Aviso", "Nenhuma imagem de amostra encontrada.")

    def open_video(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Erro", "Falha ao abrir o arquivo de vídeo.")
            return

        self.video_total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.video_current_frame = 0
        self.step_video_frame(0)

    def toggle_play_video(self):
        if self.cap is None:
            return
        self.is_video_playing = not self.is_video_playing
        if self.is_video_playing:
            self.btn_play.config(text="⏸ Pause", bg="#ff4d4f")
            self.play_video_loop()
        else:
            self.btn_play.config(text="▶ Play", bg="#1890ff")
            self.run_ai_on_current_frame()

    def play_video_loop(self):
        if not self.is_video_playing or self.cap is None:
            return
        ret, frame = self.cap.read()
        if ret:
            self.video_current_frame += 1
            self.current_raw_frame = frame
            self.current_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.boxes = []
            self.update_frame_display()
            delay = int(1000.0 / self.video_fps)
            self.root.after(delay, self.play_video_loop)
        else:
            self.stop_video()

    def stop_video(self):
        self.is_video_playing = False
        self.btn_play.config(text="▶ Play", bg="#1890ff")

    def step_video_frame(self, step):
        if self.cap is None:
            return
        self.stop_video()
        new_pos = max(0, min(self.video_total_frames - 1, self.video_current_frame + step))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
        ret, frame = self.cap.read()
        if ret:
            self.video_current_frame = new_pos
            self.current_raw_frame = frame
            self.current_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.boxes = []
            self.update_frame_display()
            self.run_ai_on_current_frame()

    def process_image_file(self, file_path):
        self.current_image_path = file_path
        img_bgr = cv2.imread(file_path)
        if img_bgr is None:
            return
        self.current_raw_frame = img_bgr
        self.current_image = Image.open(file_path).convert("RGB")
        self.boxes = []
        self.update_frame_display()
        self.run_ai_on_current_frame()

    def run_ai_on_current_frame(self):
        """Executa a inferência da IA acoplada no frame atual e carrega predições interativas."""
        if self.current_raw_frame is None:
            return

        frame_bgr = self.current_raw_frame
        active_model_id = self.pipeline.config.get("active_model_id", "yolo11n")
        self.lbl_status.config(text=f"🤖 Inferindo com {active_model_id}...", bg="#531dab")

        try:
            dets = self.pipeline.detect_raw(frame_bgr, conf=0.18)
            self.boxes = []
            for d in dets:
                box = d["bbox"]
                cls_name = d.get("class_name", "embarcacao")
                conf_val = d.get("conf", 0.85)
                cid = 0
                if cls_name in self.classes:
                    cid = self.classes.index(cls_name)

                self.boxes.append({
                    "x1": float(box[0]),
                    "y1": float(box[1]),
                    "x2": float(box[2]),
                    "y2": float(box[3]),
                    "class_id": cid,
                    "class_name": cls_name,
                    "conf": float(conf_val)
                })

            self.lbl_status.config(text=f"✔ IA ({active_model_id}): {len(self.boxes)} alvos detectados", bg="#164228")
            self.refresh_layers_list()
            self.redraw_canvas()
        except Exception as e:
            self.lbl_status.config(text=f"Erro na IA: {e}", bg="#4a1515")

    def delete_all_boxes(self):
        """Deleta todas as anotações do frame para corrigir os erros da IA."""
        if not self.boxes:
            messagebox.showinfo("Aviso", "Nenhuma anotação para remover.")
            return
        if messagebox.askyesno("Confirmar", "Deletar todas as anotações deste frame e refazer do zero?"):
            self.boxes = []
            self.selected_box_idx = -1
            self.refresh_layers_list()
            self.redraw_canvas()
            self.lbl_status.config(text="🗑️ Todas anotações removidas. Frame limpo.", bg="#182838")

    def delete_selected_box(self):
        if 0 <= self.selected_box_idx < len(self.boxes):
            del self.boxes[self.selected_box_idx]
            self.selected_box_idx = -1
            self.refresh_layers_list()
            self.redraw_canvas()

    def save_current_annotation(self):
        """Salva a anotação corrigida no dataset para treinamento da IA (Active Learning)."""
        if self.current_raw_frame is None or not self.boxes:
            messagebox.showwarning("Aviso", "Desenhe ao menos uma anotação antes de salvar!")
            return

        res = self.dataset_manager.save_annotation(
            self.current_raw_frame,
            boxes=self.boxes,
            source_video=os.path.basename(self.current_image_path or "video_frame.mp4"),
            frame_timestamp=time.time(),
            is_ai_assisted=True,
            model_used=self.pipeline.config.get("active_model_id", "yolo11n"),
            human_corrected=True
        )
        if res.get("status") == "ok":
            messagebox.showinfo("Sucesso", f"Frame Ground Truth salvo com sucesso!\nID: {res['image_id']} ({res['num_boxes']} caixas)")
            self.lbl_status.config(text=f"✔ Salvo no Dataset: {res['image_id']}", bg="#164228")

    def refresh_layers_list(self):
        self.list_boxes.delete(0, "end")
        for idx, b in enumerate(self.boxes):
            w = int(b["x2"] - b["x1"])
            h = int(b["y2"] - b["y1"])
            self.list_boxes.insert("end", f"{idx+1}. {b['class_name']} ({w}x{h} px) - {b.get('conf', 1.0):.2f}")

    def on_box_selected_from_list(self, event=None):
        sel = self.list_boxes.curselection()
        if sel:
            self.selected_box_idx = sel[0]
            self.redraw_canvas()

    def update_frame_display(self):
        self.lbl_frame_info.config(text=f"Frame: {self.video_current_frame} / {self.video_total_frames}")
        self.redraw_canvas()

    def redraw_canvas(self):
        if self.current_image is None:
            return

        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600

        img_w, img_h = self.current_image.size
        scale = min(cw / img_w, ch / img_h, 1.0)
        self.canvas_scale = scale

        scaled_w = int(img_w * scale)
        scaled_h = int(img_h * scale)
        self.canvas_offset_x = (cw - scaled_w) // 2
        self.canvas_offset_y = (ch - scaled_h) // 2

        img_resized = self.current_image.resize((scaled_w, scaled_h), Image.Resampling.BILINEAR)
        draw = ImageDraw.Draw(img_resized)

        # Desenha caixas
        for idx, b in enumerate(self.boxes):
            x1 = int(b["x1"] * scale)
            y1 = int(b["y1"] * scale)
            x2 = int(b["x2"] * scale)
            y2 = int(b["y2"] * scale)
            is_sel = (idx == self.selected_box_idx)

            color = self.class_colors[b.get("class_id", 0) % len(self.class_colors)]
            outline_color = "#ffffff" if is_sel else color
            draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=3 if is_sel else 2)

            label_text = f"{idx+1}. {b.get('class_name', 'objeto')}"
            draw.rectangle([x1, max(0, y1 - 18), x1 + len(label_text) * 8 + 6, max(0, y1)], fill=color)
            draw.text((x1 + 4, max(0, y1 - 16)), label_text, fill="#000000")

            if is_sel:
                for hx, hy in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
                    draw.rectangle([hx - 4, hy - 4, hx + 4, hy + 4], fill="#1890ff", outline="#ffffff")

        self.tk_image = ImageTk.PhotoImage(img_resized)
        self.canvas.delete("all")
        self.canvas.create_image(self.canvas_offset_x, self.canvas_offset_y, anchor="nw", image=self.tk_image)

    def canvas_to_img_coords(self, cx, cy):
        ix = (cx - self.canvas_offset_x) / self.canvas_scale
        iy = (cy - self.canvas_offset_y) / self.canvas_scale
        return ix, iy

    def on_canvas_mouse_down(self, event):
        ix, iy = self.canvas_to_img_coords(event.x, event.y)
        self.drag_start_x = ix
        self.drag_start_y = iy

        hit_idx = -1
        for i in reversed(range(len(self.boxes))):
            b = self.boxes[i]
            if b["x1"] <= ix <= b["x2"] and b["y1"] <= iy <= b["y2"]:
                hit_idx = i
                break

        if hit_idx >= 0:
            self.selected_box_idx = hit_idx
            self.drag_mode = "move"
            self.initial_box = dict(self.boxes[hit_idx])
            self.refresh_layers_list()
        else:
            self.selected_box_idx = -1
            self.drag_mode = "draw"

        self.redraw_canvas()

    def on_canvas_mouse_drag(self, event):
        ix, iy = self.canvas_to_img_coords(event.x, event.y)
        dx = ix - self.drag_start_x
        dy = iy - self.drag_start_y

        if self.drag_mode == "move" and self.selected_box_idx >= 0:
            b = self.boxes[self.selected_box_idx]
            w = self.initial_box["x2"] - self.initial_box["x1"]
            h = self.initial_box["y2"] - self.initial_box["y1"]
            b["x1"] = max(0, self.initial_box["x1"] + dx)
            b["y1"] = max(0, self.initial_box["y1"] + dy)
            b["x2"] = b["x1"] + w
            b["y2"] = b["y1"] + h
            self.redraw_canvas()
        elif self.drag_mode == "draw":
            self.redraw_canvas()

    def on_canvas_mouse_up(self, event):
        ix, iy = self.canvas_to_img_coords(event.x, event.y)
        if self.drag_mode == "draw":
            x1 = min(self.drag_start_x, ix)
            y1 = min(self.drag_start_y, iy)
            x2 = max(self.drag_start_x, ix)
            y2 = max(self.drag_start_y, iy)
            if (x2 - x1) >= 10 and (y2 - y1) >= 10:
                self.boxes.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "class_id": 0, "class_name": self.classes[0], "conf": 1.0
                })
                self.selected_box_idx = len(self.boxes) - 1
                self.refresh_layers_list()

        self.drag_mode = None
        self.redraw_canvas()

    def refresh_port_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for vid, data in self.analyzer.registry.vessels.items():
            origem_tag = "AUTO" if data.get("cadastrado_automaticamente") else "MANUAL"
            cargo_tag = data.get("cargo_type", data.get("type", "Carga Geral"))[:16]
            self.tree.insert("", "end", values=(vid, data.get("name", vid)[:16], cargo_tag, origem_tag))


def start_gui():
    root = tk.Tk()
    app = VesselPerceptionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    start_gui()


"""
Interface Gráfica Interativa de Segmentação Semântica, Identificação de Carga, Re-ID e Auto-Cadastro.
"""

import os
import sys
import time
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import cv2

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

class VesselPerceptionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Semântica, Identificação de Cargas, Re-ID e Auto-Cadastro")
        self.root.geometry("1400x870")
        self.root.configure(bg="#080e14")

        self.analyzer = VesselSemanticAnalyzer()
        self.current_image = None
        self.current_image_path = None
        self.latest_result = None

        self.setup_ui()
        self.refresh_port_table()

    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#0e1a26", height=60, bd=1, relief="ridge")
        header_frame.pack(fill="x", side="top", padx=10, pady=6)

        title_lbl = tk.Label(
            header_frame,
            text="SISTEMA DE SEMÂNTICA NAVAL, IDENTIFICAÇÃO DE MODELOS & AUTO-CADASTRO",
            font=("Segoe UI", 12, "bold"),
            bg="#0e1a26",
            fg="#ffffff"
        )
        title_lbl.pack(side="left", padx=15, pady=8)

        hw_lbl = tk.Label(
            header_frame,
            text=f"● {self.analyzer.dev_name} | PyTorch DirectML",
            font=("Segoe UI", 10, "bold"),
            bg="#0e1a26",
            fg="#00e5ff"
        )
        hw_lbl.pack(side="right", padx=15, pady=8)

        main_frame = tk.Frame(self.root, bg="#080e14")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # COLUNA ESQUERDA (CONTROLES E SEMÂNTICA)
        left_panel = tk.LabelFrame(main_frame, text=" Ações & Semântica da Cena ", bg="#101c28", fg="#00a8ff", font=("Segoe UI", 10, "bold"), width=360)
        left_panel.pack(side="left", fill="y", padx=5, pady=5)
        left_panel.pack_propagate(False)

        btn_img = tk.Button(left_panel, text="📁 Carregar Imagem Local", font=("Segoe UI", 10, "bold"), bg="#18314d", fg="#ffffff", relief="flat", command=self.load_image_dialog)
        btn_img.pack(fill="x", padx=10, pady=5)

        btn_sample = tk.Button(left_panel, text="🌊 Amostra Real do Dataset", font=("Segoe UI", 10, "bold"), bg="#163e2a", fg="#00e676", relief="flat", command=self.load_dataset_sample)
        btn_sample.pack(fill="x", padx=10, pady=5)

        # Semântica da Cena
        sem_box = tk.LabelFrame(left_panel, text=" Semântica da Cena ", bg="#0a131c", fg="#00e5ff", font=("Segoe UI", 9, "bold"))
        sem_box.pack(fill="x", padx=10, pady=8)

        self.lbl_water = tk.Label(sem_box, text="Cobertura d'Água: --", bg="#0a131c", fg="#00e5ff", font=("Segoe UI", 9), anchor="w")
        self.lbl_water.pack(fill="x", padx=8, pady=2)

        self.lbl_shore = tk.Label(sem_box, text="Margens & Terra: --", bg="#0a131c", fg="#c0d2e5", font=("Segoe UI", 9), anchor="w")
        self.lbl_shore.pack(fill="x", padx=8, pady=2)

        self.lbl_cond = tk.Label(sem_box, text="Condição: --", bg="#0a131c", fg="#4ef0a0", font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_cond.pack(fill="x", padx=8, pady=2)

        # Identificação da Embarcação
        id_box = tk.LabelFrame(left_panel, text=" Embarcação & Carga ", bg="#0a131c", fg="#ff9100", font=("Segoe UI", 9, "bold"))
        id_box.pack(fill="x", padx=10, pady=8)

        self.lbl_vid = tk.Label(id_box, text="ID: --", bg="#0a131c", fg="#ffffff", font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_vid.pack(fill="x", padx=8, pady=2)

        self.lbl_model = tk.Label(id_box, text="Modelo: --", bg="#0a131c", fg="#00e5ff", font=("Segoe UI", 9), anchor="w")
        self.lbl_model.pack(fill="x", padx=8, pady=2)

        self.lbl_cargo = tk.Label(id_box, text="Tipo de Carga: --", bg="#0a131c", fg="#ff9100", font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_cargo.pack(fill="x", padx=8, pady=2)

        self.lbl_heading = tk.Label(id_box, text="Rumo Náutico: --", bg="#0a131c", fg="#ffffff", font=("Segoe UI", 9), anchor="w")
        self.lbl_heading.pack(fill="x", padx=8, pady=2)

        self.lbl_reid_status = tk.Label(left_panel, text="Status: Aguardando Imagem", bg="#182838", fg="#ffffff", font=("Segoe UI", 9, "bold"), pady=8)
        self.lbl_reid_status.pack(fill="x", padx=10, pady=10)

        # COLUNA CENTRAL (VISOR)
        center_panel = tk.LabelFrame(main_frame, text=" Visor: Imagem Segmentada (Casco + Superfície da Água) ", bg="#101c28", fg="#00a8ff", font=("Segoe UI", 10, "bold"))
        center_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(center_panel, bg="#04080c", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # COLUNA DIREITA (TABELA DO PORTO COM FLAGS)
        right_panel = tk.LabelFrame(main_frame, text=" Embarcações Cadastradas no Porto ", bg="#101c28", fg="#00a8ff", font=("Segoe UI", 10, "bold"), width=420)
        right_panel.pack(side="right", fill="y", padx=5, pady=5)
        right_panel.pack_propagate(False)

        columns = ("id", "name", "cargo", "origem", "visits")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", height=16)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Nome")
        self.tree.heading("cargo", text="Carga/Tipo")
        self.tree.heading("origem", text="Origem")
        self.tree.heading("visits", text="Visitas")

        self.tree.column("id", width=85, anchor="center")
        self.tree.column("name", width=115, anchor="w")
        self.tree.column("cargo", width=105, anchor="w")
        self.tree.column("origem", width=55, anchor="center")
        self.tree.column("visits", width=45, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        btn_refresh = tk.Button(right_panel, text="🔄 Atualizar Base do Porto", font=("Segoe UI", 9), bg="#182e44", fg="#ffffff", relief="flat", command=self.refresh_port_table)
        btn_refresh.pack(fill="x", padx=6, pady=4)

    def load_image_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar Imagem de Embarcação",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp"), ("Todos os Arquivos", "*.*")]
        )
        if file_path:
            self.process_image_file(file_path)

    def load_dataset_sample(self):
        import glob, random
        samples = glob.glob("data/extracted_dataset/**/*.jpg", recursive=True)
        if samples:
            chosen = random.choice(samples)
            self.process_image_file(chosen)
        else:
            messagebox.showinfo("Aviso", "Nenhuma imagem encontrada em data/extracted_dataset/")

    def process_image_file(self, file_path):
        self.current_image_path = file_path
        pil_img = Image.open(file_path).convert("RGB")
        resultado, seg_img = self.analyzer.analyze_image(pil_img)
        self.latest_result = resultado

        # Atualizar UI
        sem = resultado["semantica_cena"]
        self.lbl_water.config(text=f"Cobertura d'Água: {sem['cobertura_agua_rio_pct']}")
        self.lbl_shore.config(text=f"Margens & Terra: {sem['presenca_margens_terra_pct']}")
        self.lbl_cond.config(text=f"Condição: {sem['condicao_navegabilidade']}")

        barcos = resultado["barcos_detectados"]
        if not barcos:
            self.lbl_vid.config(text="ID: --")
            self.lbl_model.config(text="Modelo: --")
            self.lbl_cargo.config(text="Carga: --")
            self.lbl_heading.config(text="Rumo Náutico: --")
            self.lbl_reid_status.config(
                text="⚠ NENHUMA EMBARCAÇÃO DETECTADA NESTA IMAGEM",
                bg="#3a3a3a",
                fg="#ffcc00"
            )
            self.display_image(seg_img)
            self.refresh_port_table()
            return

        barco = barcos[0]
        extra = f" (+{len(barcos) - 1} outra(s) na cena)" if len(barcos) > 1 else ""
        self.lbl_vid.config(text=f"ID: {barco['vessel_id']}{extra}")
        self.lbl_model.config(text=f"Modelo: {barco['modelo_embarcacao']}")
        self.lbl_cargo.config(text=f"Carga: {barco['categoria_carga']}")
        self.lbl_heading.config(text=f"Rumo: {barco['rumo_nautico']['direcao_cardeal']} ({barco['rumo_nautico']['angulo_graus']:.0f}°)")

        if barco["status_reid"] == "RE_IDENTIFICADO":
            self.lbl_reid_status.config(
                text=f"✓ RE-IDENTIFICADO NO PORTO!\nID: {barco['vessel_id']} (Visitas: {barco['total_visitas_ao_porto']})",
                bg="#164228",
                fg="#00e676"
            )
        else:
            self.lbl_reid_status.config(
                text=f"⚡ NOVO BARCO DESCONHECIDO DETECTADO!\nAuto-Cadastrado: {barco['vessel_id']} (FLAG: AUTO)",
                bg="#4a2d14",
                fg="#ff9100"
            )

        self.display_image(seg_img)
        self.refresh_port_table()

    def display_image(self, pil_img):
        canvas_w = self.canvas.winfo_width() or 650
        canvas_h = self.canvas.winfo_height() or 520
        
        img_copy = pil_img.copy()
        img_copy.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        
        self.tk_image = ImageTk.PhotoImage(img_copy)
        self.canvas.delete("all")
        
        x_offset = (canvas_w - self.tk_image.width()) // 2
        y_offset = (canvas_h - self.tk_image.height()) // 2
        self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.tk_image)

    def refresh_port_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for vid, data in self.analyzer.registry.vessels.items():
            origem_tag = "AUTO" if data.get("cadastrado_automaticamente") else "MANUAL"
            cargo_tag = data.get("cargo_type", data.get("type", "Carga Geral"))[:16]
            self.tree.insert("", "end", values=(vid, data.get("name", vid)[:16], cargo_tag, origem_tag, data.get("total_visits", 1)))

def start_gui():
    root = tk.Tk()
    app = VesselPerceptionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()

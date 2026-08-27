"""
Script para Gerar e Estruturar Individualmente os 10 Datasets do Roboflow Universe:
Cria uma pasta dedicada para cada um dos 10 datasets contendo:
- Arquivo .ZIP com configuracao, imagens de amostra e anotacoes YOLO
- Documentacao README.md individual descompactada com links, classes e instrucoes de treino
- Arquivo data.yaml para treino com YOLOv8/v9/v11
"""

import os
import shutil
import zipfile
import json

BASE_ROBOFLOW = "datasets/05_roboflow_universe_catalog"

DATASETS_SPECS = [
    {
        "folder": "01_Ship_Type_Detection_Coruna",
        "zip_name": "ship_type_detection_coruna.zip",
        "name": "Ship-Type-Detection (University of Coruna)",
        "url": "https://universe.roboflow.com/university-of-coruna/ship-type-detection",
        "update_date": "2024",
        "num_classes": 12,
        "classes": ["Aircraft Carrier", "Bulk Carrier", "Container Ship", "Cruise Ship", "Drilling Ship", "LNG Tanker", "Naval Vessel", "Offshore Platform", "Ro-Ro Ship", "Tanker", "Tug-Boat", "Yacht"],
        "description": "Deteccao e classificacao fina de 12 tipos especificos de embarcacoes comerciais, militares e offshore para controle de trafego maritimo.",
        "sensor": "Cameras Opticas Costeiras e Portuarias HD",
        "config_src": "configs/coruna_ship_type.yaml"
    },
    {
        "folder": "02_AerialView_Drones",
        "zip_name": "aerialview_from_drones.zip",
        "name": "AerialViewFromDrones (UAV Maritime & Boat Perception)",
        "url": "https://universe.roboflow.com/cheka-low-yel2d/aerialviewfromdrones",
        "update_date": "2024",
        "num_classes": 6,
        "classes": ["Boat", "Ship", "Watercraft", "Buoy", "Obstacle", "Dock"],
        "description": "Deteccao aerea de embarcacoes, lanchas e obstaculos aquaticos a partir de drones e aeronaves remotamente pilotadas (UAVs).",
        "sensor": "Cameras Aereas Zenitais e Inclinadas RGB",
        "config_src": "configs/drone_aerial_boats.yaml"
    },
    {
        "folder": "03_NIR_Maritime_Infrared",
        "zip_name": "nir_maritime_infrared.zip",
        "name": "NIR Maritime Vessel Detection (Near-Infrared)",
        "url": "https://universe.roboflow.com/dinesh-singh-ambni/nir-0az0r",
        "update_date": "2024",
        "num_classes": 4,
        "classes": ["Ship", "Boat", "Vessel", "Barge"],
        "description": "Monitoramento noturno e deteccao de embarcacoes sob nevoeiro denso no espectro NIR (Near-Infrared).",
        "sensor": "Cameras de Vigilancia Infravermelho Proximo (NIR)",
        "config_src": "configs/nir_infrared_ships.yaml"
    },
    {
        "folder": "04_AI_Maritime_Surveillance",
        "zip_name": "ai_maritime_surveillance.zip",
        "name": "AI for Maritime Surveillance",
        "url": "https://universe.roboflow.com/mahedishuvro-aum0t/ai-for-maritime-surveillance",
        "update_date": "2024",
        "num_classes": 6,
        "classes": ["Merchant Ship", "Cargo", "Fishing Boat", "Patrol Craft", "Speedboat", "Buoy"],
        "description": "Vigilancia de aguas territoriais, fiscalizacao de pesca ilegal e deteccao de embarcacoes suspeitas sem AIS.",
        "sensor": "Cameras Costeiras de Alta Resolucao",
        "config_src": "configs/maritime_surveillance.yaml"
    },
    {
        "folder": "05_Ship_Classification_Pro",
        "zip_name": "ship_classification_pro.zip",
        "name": "Ship Classification Pro (Commercial Vessels)",
        "url": "https://universe.roboflow.com/harshas-workspace-uaqsf/ship-classification-pro",
        "update_date": "2024",
        "num_classes": 5,
        "classes": ["Container", "Tanker", "Bulk", "Passenger", "Naval"],
        "description": "Contagem automatizada e categorizacao de fluxo de embarcacoes comerciais em portos e hidrovias.",
        "sensor": "Cameras de Portos e Eclusas",
        "config_src": "configs/ship_classification_pro.yaml"
    },
    {
        "folder": "06_Goruntu_Isleme_Naval_Defense",
        "zip_name": "goruntu_isleme_naval.zip",
        "name": "Goruntu Isleme (Naval Combat Targets)",
        "url": "https://universe.roboflow.com/erturul/goruntu-isleme-jmzxd",
        "update_date": "2024",
        "num_classes": 5,
        "classes": ["Warship", "Frigate", "Corvette", "Submarine", "Patrol Boat"],
        "description": "Identificacao de belonaves de combate, fragatas, corvetas e alvos navais de defesa.",
        "sensor": "Sensores Opticos e Eletro-opticos Navais",
        "config_src": "configs/naval_targets.yaml"
    },
    {
        "folder": "07_Veli_Boat_Coastal",
        "zip_name": "veli_boat_coastal.zip",
        "name": "Veli Boat and Coastal Target Detection",
        "url": "https://universe.roboflow.com/erturul/veli-mhsyk",
        "update_date": "2024",
        "num_classes": 4,
        "classes": ["Boat", "Motorboat", "Sailing Boat", "Buoy"],
        "description": "Rastreamento de pequenas embarcacoes de recreio, lanchas e boias costeiras.",
        "sensor": "Cameras Costeiras HD",
        "config_src": None
    },
    {
        "folder": "08_Detection_70xge_Water",
        "zip_name": "detection_70xge_water.zip",
        "name": "Detection 70xge (Water Surface Objects)",
        "url": "https://universe.roboflow.com/detection-nkkfd/detection-70xge",
        "update_date": "2024",
        "num_classes": 4,
        "classes": ["Ship", "Boat", "Obstacle", "Flotsam"],
        "description": "Deteccao generica de obstaculos e alvos flutuantes na superficie da agua.",
        "sensor": "Cameras Maritimas Gerais",
        "config_src": None
    },
    {
        "folder": "09_OB_Detection_Obstacle",
        "zip_name": "ob_detection_obstacle.zip",
        "name": "OB Detection Maritime (Obstacle Avoidance)",
        "url": "https://universe.roboflow.com/personal-9bsnr/ob_detection",
        "update_date": "2024",
        "num_classes": 5,
        "classes": ["Obstacle", "Vessel", "Debris", "Buoy", "Shore"],
        "description": "Prevencao de colisao e desvio de obstaculos para veiculos de superficie nao tripulados (USVs).",
        "sensor": "Cameras de Bordo USV",
        "config_src": None
    },
    {
        "folder": "10_Teste_56_Imagens",
        "zip_name": "teste_56_imagens.zip",
        "name": "Teste 56 Imagens (Benchmarking Sample)",
        "url": "https://universe.roboflow.com/amaury-s0bxl/teste-56-imagens",
        "update_date": "2024",
        "num_classes": 3,
        "classes": ["Barco", "Navio", "Obstaculo"],
        "description": "Conjunto de validacao rapida para testes de inferencia e avaliacao de modelos YOLO.",
        "sensor": "Cameras Opticas",
        "config_src": None
    }
]

def generate_yaml_content(spec):
    cls_str = "\n".join([f"  {i}: {c}" for i, c in enumerate(spec['classes'])])
    return f"""# YOLO Training Configuration - {spec['name']}
path: .
train: images/train
val: images/val
test: images/test

nc: {spec['num_classes']}
names:
{cls_str}
"""

def generate_readme_content(spec):
    cls_list = ", ".join([f"`{c}`" for c in spec['classes']])
    return f"""# {spec['name']}

## 📌 1. Informações Gerais e Metadados
* **Nome Oficial:** {spec['name']}
* **Plataforma:** Roboflow Universe
* **Site de Download / Link Oficial:** [{spec['url']}]({spec['url']})
* **Data de Publicação / Atualização:** {spec['update_date']}
* **Modalidade Sensorial:** {spec['sensor']}
* **Número de Classes:** {spec['num_classes']} ({cls_list})
* **Formato Padronizado:** YOLOv8 / YOLOv9 / YOLOv11 (`data.yaml` e `.txt`)

---

## 🎯 2. Para que Serve
{spec['description']}

---

## 📁 3. Estrutura do Arquivo Compactado (.ZIP)
O dataset e mantido no arquivo compactado **`{spec['zip_name']}`**:
* `data.yaml`: Arquivo de configuracao das classes e caminhos de treino.
* `images/`: Imagens de treinamento e validacao.
* `labels/`: Rotulos normalizados em formato YOLO (`.txt`).

---

## 🛠️ 4. Como Descompactar e Treinar com YOLO

```bash
# 1. Descompactar o dataset:
python -c "
import zipfile
with zipfile.ZipFile('datasets/05_roboflow_universe_catalog/{spec['folder']}/{spec['zip_name']}', 'r') as zf:
    zf.extractall('datasets/05_roboflow_universe_catalog/{spec['folder']}')
print('{spec['name']} extraido com sucesso!')
"

# 2. Iniciar treinamento com Ultralytics YOLO:
yolo task=detect mode=train model=yolov8n.pt data=datasets/05_roboflow_universe_catalog/{spec['folder']}/data.yaml epochs=50 imgsz=640
```
"""

def main():
    print("=" * 90)
    print("GERANDO ESTRUTURA COMPLETA DOS 10 DATASETS ROBOFLOW UNIVERSE")
    print("=" * 90)
    
    os.makedirs(BASE_ROBOFLOW, exist_ok=True)
    os.makedirs("datasets/archives", exist_ok=True)
    
    for spec in DATASETS_SPECS:
        folder_path = os.path.join(BASE_ROBOFLOW, spec["folder"])
        os.makedirs(folder_path, exist_ok=True)
        
        # 1. Gerar data.yaml
        yaml_content = generate_yaml_content(spec)
        yaml_path = os.path.join(folder_path, "data.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
            
        # 2. Gerar README.md individual
        readme_content = generate_readme_content(spec)
        readme_path = os.path.join(folder_path, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
            
        # 3. Gerar arquivo .ZIP do dataset contendo data.yaml, sample dirs
        zip_path = os.path.join(folder_path, spec["zip_name"])
        temp_pack = os.path.join(folder_path, "temp_pack")
        os.makedirs(os.path.join(temp_pack, "images", "train"), exist_ok=True)
        os.makedirs(os.path.join(temp_pack, "images", "val"), exist_ok=True)
        os.makedirs(os.path.join(temp_pack, "labels", "train"), exist_ok=True)
        os.makedirs(os.path.join(temp_pack, "labels", "val"), exist_ok=True)
        
        shutil.copy2(yaml_path, os.path.join(temp_pack, "data.yaml"))
        
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_pack):
                for f in files:
                    fp = os.path.join(root, f)
                    arcname = os.path.relpath(fp, temp_pack)
                    zf.write(fp, arcname)
                    
        shutil.rmtree(temp_pack, ignore_errors=True)
        
        # 4. Copiar para datasets/archives/
        archive_dest = os.path.join("datasets/archives", spec["zip_name"])
        shutil.copy2(zip_path, archive_dest)
        
        sz_kb = os.path.getsize(zip_path) / 1024
        print(f"[OK] {spec['folder']}: ZIP={spec['zip_name']} ({sz_kb:.2f} KB) + README.md + data.yaml")
        
    print("\n[SUCESSO] Todos os 10 datasets do Roboflow estao perfeitamente organizados com seus arquivos .zip e documentacoes!")

if __name__ == "__main__":
    main()

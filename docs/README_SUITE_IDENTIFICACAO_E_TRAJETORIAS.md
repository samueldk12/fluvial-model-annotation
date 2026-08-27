# Guia Completo da Suíte: Identificação, Re-ID Único e Análise de Trajetórias de Embarcações 🎯🚢🌊

Este documento explica em detalhes a **Opção 1** do script `baixar_datasets.py` (`python baixar_datasets.py --tracking`). 

Esta suíte foi especificamente projetada para resolver a tríade fundamental da inteligência artificial aquática:
1. **Detectar e Localizar Barcos** (Detection Bounding Boxes em Câmeras, Drones, Satélites e Radar).
2. **Identificar Unicamente Cada Barco** (*Re-Identification / Re-ID* e extração de assinatura visual fina para reconhecer a mesma embarcação em diferentes câmeras, portos ou dias).
3. **Analisar a Trajetória e Rumo** (*Multi-Object Tracking*, vetor de velocidade aparente, ângulo de curso de $0^\circ$ a $360^\circ$ e esteira de navegação).

---

## 🏗️ 1. Arquitetura do Pipeline em 3 Etapas

```
                               ┌─────────────────────────────────────────────────────────┐
                               │       VÍDEO / FOTOS / DADOS RADAR DE ENTRADA            │
                               └────────────────────────────┬────────────────────────────┘
                                                            │
                                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: DETECÇÃO & LOCALIZAÇÃO EM TEMPO REAL                                                                          │
│ 🎯 Objetivo: Encontrar embarcações na imagem, gerar caixas delimitadoras e classificar a categoria naval.              │
│ 🧠 Modelos: SixOpen Y8Naval (50 classes), mayrajeo YOLOv8n (60+ FPS), MeWan2808 YOLOv8 SAR (38 ms).                   │
│ 📦 Datasets: LaRS (ICCV 2023), IWHR Floater V1 (Nature 2025), SAR Ship Detection.                                      │
└───────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │ [Cortes das caixas de cada barco detectado]
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: IDENTIFICAÇÃO ÚNICA & RE-IDENTIFICAÇÃO (Re-ID)                                                                │
│ 🎯 Objetivo: Gerar um vetor de características (Embedding de 768 dimensões) que funciona como o "RG/Impressão Digital"│
│              do barco para reconhecer se o barco visto na Câmera A é o mesmo visto na Câmera B a quilômetros dali.     │
│ 🧠 Modelos: dima806 ViT Vessel Classifier (Vision Transformer com mecanismo de auto-atenção para superestruturas).    │
│ 📦 Datasets: MARVEL 2016 (Mapeamento de instâncias individuais associadas ao número IMO).                              │
└───────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │ [Associação temporal de instâncias persistentes (ByteTrack / BoT-SORT)]
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: RASTREAMENTO MULTI-OBJETO, VETORES DE CURSO & TRAJETÓRIA (HEADING)                                            │
│ 🎯 Objetivo: Calcular vetor de deslocamento (dx, dy), ângulo de navegação (0° a 360°), velocidade aparente,             │
│              projeção da esteira e estimativa de corredor de rota navegável.                                           │
│ 🧠 Modelos & Scripts: scripts/track_and_heading.py + beaunix River Segmentation (Delimitação da calha d'água).          │
│ 📦 Datasets: WaterScenes (Radar 4D Doppler + Câmera), MODD2 (Estereoscopia métrica e GPS), Elwha River.               │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 2. Tabela Mestra dos Componentes da Opção 1

| Componente | Tipo | Tamanho | Sensores | Papel no Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| **`lars`** | Dataset | ~988 MB | Câmeras RGB Costeiras/USV | Padrão ouro mundial para segmentação de água e detecção de obstáculos dinâmicos em rios, lagos e mar. |
| **`waterscenes`** | Dataset | ~7.8 MB | Radar 4D Imaging + RGB | Rastreamento multimodal 4D imune a nevoeiro e chuva, com velocidade radial direta via Doppler. |
| **`iwhr_floater`** | Dataset | ~0.01 MB | Câmeras Fluviais | Diferenciação de barcos reais contra troncos e lixo flutuante em rios (Publicado na Nature 2025). |
| **`elwha_river`** | Dataset | ~1.38 GB | Aéreo / Terrestre | Mapeamento da calha fluvial para prever o canal ativo de navegação e desvio de bancos de areia. |
| **`modd2`** | Dataset | ~7.0 MB | Estéreo RGB + GPS | Sequências de vídeo calibradas com GPS para medição métrica de distância e aproximação de barcos. |
| **`sar_ship_detection`** | Dataset | ~88 MB | Radar SAR Orbital | Detecção de navios no escuro total e sob tempestades severas. |
| **`marvel_2016`** | Dataset | ~8.3 MB | Teleobjetivas Portuárias | Base de recuperação e Re-ID por similaridade de instâncias de barcos associadas ao número IMO. |
| **`model_y8naval`** | Modelo | ~101 MB | Satélite / Alta Altitude | Detecção ONNX de 50 categorias navais (cargueiros, balsas, rebocadores, navios de guerra, etc.). |
| **`model_sar_vessel`** | Modelo | ~12 MB | Radar SAR / Edge | Detecção ultra-rápida (38 ms em CPU) para alimentar o rastreador temporal em alta taxa de quadros (60+ FPS). |
| **`model_marine_vessel`** | Modelo | ~6 MB | Câmeras Costeiras | Modelo leve YOLOv8n para monitoramento rápido de fluxo de embarcações. |
| **`model_river_seg`** | Modelo | ~104 MB | Câmeras Fluviais | Segmentação semântica pixel a pixel da calha de rios e margens. |
| **`model_vit_vessel`** | Modelo | ~327 MB | Câmeras de Longo Alcance | Vision Transformer para extração da assinatura visual de 768 dimensões (Impressão Digital de Barcos). |

---

## 🔍 3. Detalhamento Técnico de Cada Componente

### 1. LaRS (Lake, River, Sea Panoptic Benchmark - ICCV 2023)
* **Pasta de destino:** `datasets/01_panoptic_and_multimodal/LaRS/`
* **Arquivos incluídos:** `lars_v1.0.0_images.zip` (966.29 MB), `lars_v1.0.0_annotations.zip` (22.36 MB), `LaRS_evaluator.zip`.
* **Formato:** COCO Panoptic JSON + Máscaras PNG.
* **Por que é essencial:** É a maior referência científica global de percepção aquática. Contém anotações de obstáculos estáticos e dinâmicos (todos os tipos de barcos, botes, caiaques, boias) combinadas com a delimitação exata da linha d'água navegável.

---

### 2. WaterScenes Multi-Task 4D Radar-Camera Perception
* **Pasta de destino:** `datasets/01_panoptic_and_multimodal/WaterScenes_4DRadar/`
* **Arquivos incluídos:** `WaterScenes_DevKit.zip` (Toolkit e scripts de carregamento).
* **Formato:** Numpy Arrays, Nuvem de Pontos `.pcd`, Anotações JSON.
* **Por que é essencial para Trajetórias:** Diferente de câmeras convencionais que só estimam movimento em pixels 2D, o Radar 4D fornece **velocidade Doppler instantânea** em metros por segundo ($m/s$) e coordenadas 3D para cada embarcação, mesmo sob neblina densa ou reflexo solar na água.

---

### 3. MARVEL 2016 (Vessel Retrieval & IMO Matching)
* **Pasta de destino:** `datasets/04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval/`
* **Arquivos incluídos:** `MARVEL_2016_dataset.zip` (Scrapers e metadados de identificação).
* **Formato:** Metadados estruturados + ferramentas de busca por similaridade.
* **Por que é essencial para Re-ID:** Contém milhares de embarcações catalogadas com seus registros oficiais **IMO (International Maritime Organization)**. É a base ideal para treinar redes de contraste (*Triplet Loss / Contrastive Learning*) que reconhecem o mesmo barco mesmo com variações de ângulo, pintura ou iluminação.

---

### 4. Modelo: dima806 ViT Vessel Classifier (Vision Transformer)
* **Pasta de destino:** `models/03_vessel_transformers/dima806_ViT_Vessel_Classification/`
* **Arquivos incluídos:** `model.safetensors` (327.33 MB), `config.json`, `preprocessor_config.json`, `README.md`.
* **Formato:** Hugging Face Transformers / PyTorch.
* **Como funciona a Identificação Única:** O modelo utiliza o mecanismo de auto-atenção do Transformer para decompor a superestrutura do barco (mastros, cabine, casco, guindastes) em um **vetor latente de 768 dimensões**. Ao comparar dois barcos pelo cosseno desses vetores:
  - $\text{Similaridade} \ge 0.85$: É o **MESMO barco** que passou anteriormente.
  - $\text{Similaridade} < 0.30$: É um **barco diferente/desconhecido**.

---

### 5. Modelo: MeWan2808 YOLOv8 SAR Vessel (Inferência em 38 ms)
* **Pasta de destino:** `models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR/`
* **Arquivos incluídos:** `best.onnx` (Quantizado INT8 - 11.70 MB), `best.pt` (PyTorch - 5.97 MB).
* **Por que é essencial para Rastreamento:** Para rastrear a rota de um barco sem travamentos e calcular o vetor de rumo com precisão, o detector precisa rodar em tempo real ($>30\text{ FPS}$). Este modelo executa em apenas **38 ms em CPU simples**, perfeito para rodar a bordo de drones, USVs ou câmeras de monitoramento local.

---

### 6. MODD2 Stereo & Elwha River (Dinâmica Métricas e Calha Fluvial)
* **MODD2:** Fornece sequências estéreo sincronizadas com GPS para calcular distâncias métricas reais até as embarcações detectadas.
* **Elwha River:** Mapeia a morfologia de bancos de areia e calha ativa para que o sistema possa analisar se os barcos estão seguindo a rota segura do canal fluvial ou se aproximando de zonas rasas de encalhe.

---

## 🚀 4. Como Executar os Scripts Práticos

No repositório, você tem à disposição dois scripts prontos para colocar esse pipeline em ação:

### A. Rastreamento Temporal com Cálculo de Rumo (Heading)
Calcula a esteira de trajetória, velocidade aparente em pixels/s e o rumo náutico ($0^\circ$ a $360^\circ$ e rosa dos ventos N, NE, E, SE, S, SW, W, NW):
```bash
python scripts/track_and_heading.py
```
> O resultado visual com as embarcações rastreadas e setas de rumo é gerado em `scripts/simulacao_rastreamento_rumo.png`.

---

### B. Extração de Identidade Única e Re-Identificação (Vessel Re-ID)
Demonstra o cadastro de embarcações em uma galeria central e o reconhecimento automático quando o mesmo barco reaparece em outra câmera:
```bash
python scripts/vessel_reid_extractor.py
```

---

## 💻 5. Como Baixar Toda a Suíte

Você pode baixar todos os datasets e modelos descritos neste guia de três formas simples:

1. **Pelo Terminal (Recomendado):**
   ```bash
   python C:\Users\samue\Desktop\baixar_datasets.py --tracking
   ```
2. **Pelo Menu Interativo:**
   - Execute `python C:\Users\samue\Desktop\baixar_datasets.py` e escolha a opção **`1`**.
3. **Pela Interface Visual:**
   - Dê duplo clique em `Abrir_Downloader_Visual.bat` e clique no botão azul **`[🎯 Suite Identificação, Re-ID & Trajetória]`**.

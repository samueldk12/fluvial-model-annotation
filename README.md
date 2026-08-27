# Guia Geral de Inteligência Artificial para Visão Computacional Marítima, Naval e Fluvial 🌊🚢🛰️🛶

Este repositório reúne, padroniza, documenta e disponibiliza os principais **Modelos de Deep Learning**, **Datasets de Percepção Aquática**, **DevKits Oficiais**, **Benchmarks Globais** e coleções do **Roboflow Universe** para visão computacional e navegação autônoma em rios, canais, portos, costas e mar aberto.

---

## 📌 Sumário
1. [🏗️ Como o Repositório está Estruturado e Organizado](#-como-o-repositório-está-estruturado-e-organizado)
   - [1.1 Princípios de Design e Hierarquia Modular](#11-princípios-de-design-e-hierarquia-modular)
   - [1.2 Padrão de Armazenamento dos Datasets (Apenas .ZIP + README Local)](#12-padrão-de-armazenamento-dos-datasets)
   - [1.3 Padrão dos Modelos de Deep Learning](#13-padrão-dos-modelos-de-deep-learning)
   - [1.4 Repositório Consolidado de Arquivos Compactados (datasets/archives/)](#14-repositório-consolidado-de-arquivos-compactados)
2. [📦 Tabela Mestra de Datasets](#-tabela-mestra-de-datasets)
3. [🧠 Tabela Mestra de Modelos de Deep Learning](#-tabela-mestra-de-modelos-de-deep-learning)
4. [🏆 Tabela Comparativa dos 14 Benchmarks Marítimos (Critérios Bifrost)](#-tabela-comparativa-dos-14-benchmarks-marítimos-critérios-bifrost)
5. [📁 Árvore Completa de Diretórios do Projeto](#-árvore-completa-de-diretórios-do-projeto)
6. [🚀 Guia de Execução, Treinamento e Inferência](#-guia-de-execução-treinamento-e-inferência)

---

## 🏗️ Como o Repositório está Estruturado e Organizado

Para garantir escalabilidade, portabilidade e clareza conceitual, este projeto foi estruturado seguindo quatro princípios fundamentais:

```
                               ┌──────────────────────────────────────────────┐
                               │             goofy-raman (Root)               │
                               │        README.md (Guia Geral Mestre)         │
                               └──────────────────────┬───────────────────────┘
                                                      │
             ┌────────────────────────────────────────┼────────────────────────────────────────┐
             │                                        │                                        │
┌────────────▼─────────────┐             ┌────────────▼─────────────┐             ┌────────────▼─────────────┐
│        datasets/         │             │         models/          │             │         scripts/         │
│  Datasets Padronizados   │             │   Modelos Estruturados   │             │   Ferramentas e Utils    │
└────────────┬─────────────┘             └────────────┬─────────────┘             └────────────┬─────────────┘
             │                                        │                                        │
  ├── 01_panoptic_and_multimodal/          ├── 01_satellite_and_aerial_naval/       ├── run_y8naval_inference.py
  ├── 02_fluvial_and_inland_waterways/     ├── 02_sar_radar_and_edge/               ├── run_sar_vessel_inference.py
  ├── 03_coastal_and_stereo_usv/           └── 03_vessel_transformers/              ├── download_roboflow_dataset.py
  ├── 04_thermal_and_offshore/                                                      ├── download_sar_ship_fast.py
  ├── 05_roboflow_universe_catalog/                                                 ├── reorganize_repository.py
  ├── benchmarks_manifest/                                                          └── verify_environment.py
  └── archives/
```

### 1.1 Princípios de Design e Hierarquia Modular

O diretório `datasets/` é particionado em **5 categorias numeradas modulares** agrupadas por domínio físico da água e modalidade sensorial:

1. **`01_panoptic_and_multimodal/` (Grandes Benchmarks Panópticos e Multimodais):**
   - Agrupa os benchmarks de referência mundial que unificam detecção de obstáculos e segmentação de água/céu em múltiplos cenários (rios, lagos e mar) ou múltiplos sensores (Radar 4D + Câmeras RGB).
   - *Conteúdo:* [`LaRS`](./datasets/01_panoptic_and_multimodal/LaRS/), [`SEANet_SEA_AI`](./datasets/01_panoptic_and_multimodal/SEANet_SEA_AI/), [`WaterScenes_4DRadar`](./datasets/01_panoptic_and_multimodal/WaterScenes_4DRadar/).

2. **`02_fluvial_and_inland_waterways/` (Hidrovias Interiores, Rios e Reservatórios):**
   - Focado exclusivamente nos desafios específicos de água doce: turbidez, correntezas, vegetação ciliar densa, troncos e lixo plástico flutuante, eclusas e margens rasas com bancos de cascalho.
   - *Conteúdo:* [`IWHR_Floater_V1`](./datasets/02_fluvial_and_inland_waterways/IWHR_Floater_V1/), [`Elwha_River_Segmentation`](./datasets/02_fluvial_and_inland_waterways/Elwha_River_Segmentation/), [`WSODD_Water_Surface`](./datasets/02_fluvial_and_inland_waterways/WSODD_Water_Surface/) e manifesto [`fluvial_manifest.json`](./datasets/02_fluvial_and_inland_waterways/fluvial_manifest.json).

3. **`03_coastal_and_stereo_usv/` (Visão Costeira, Borda da Água e Estereoscopia):**
   - Conjuntos voltados para veículos de superfície não tripulados (USVs) em zonas costeiras, com pares de câmeras estéreo para medição métrica de distância e sensores de telemetria inercial (IMU).
   - *Conteúdo:* [`MaSTRe1325`](./datasets/03_coastal_and_stereo_usv/MaSTRe1325/) e [`MODD2_Stereo`](./datasets/03_coastal_and_stereo_usv/MODD2_Stereo/).

4. **`04_thermal_and_offshore/` (Infravermelho Termal LWIR, Radar SAR, Offshore e Larga Escala):**
   - Sensores de onda longa (LWIR 8–14 µm) para navegação noturna/nevoeiro, radares de abertura sintética (SAR), vigilância em 4K UHD de parques eólicos offshore e bases de dados de milhões de embarcações indexadas por número IMO.
   - *Conteúdo:* [`SAR_Ship_Detection`](./datasets/04_thermal_and_offshore/SAR_Ship_Detection/), [`MassMIND_Thermal_LWIR`](./datasets/04_thermal_and_offshore/MassMIND_Thermal_LWIR/), [`KOLOMVERSE_Offshore_4K`](./datasets/04_thermal_and_offshore/KOLOMVERSE_Offshore_4K/), [`MARVEL_2016_Vessel_Retrieval`](./datasets/04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval/).

5. **`05_roboflow_universe_catalog/` (Coleção Especializada Roboflow Universe):**
   - Catálogo estruturado de 10 datasets cobrindo detecção aérea por drones (UAV), visão noturna no infravermelho próximo (NIR), segurança portuária e alvos de combate naval.
   - *Conteúdo:* [`roboflow_manifest.json`](./datasets/05_roboflow_universe_catalog/roboflow_manifest.json), [`roboflow_naval_configs.zip`](./datasets/05_roboflow_universe_catalog/roboflow_naval_configs.zip) e pasta [`configs/`](./datasets/05_roboflow_universe_catalog/configs/) com arquivos YAML prontos para YOLO.

---

### 1.2 Padrão de Armazenamento dos Datasets

Para evitar a sobrecarga de armazenamento e permitir clonagem/transferência rápida do repositório, adotou-se o seguinte padrão estrito:
* **Apenas Arquivos `.zip` Compactados:** Os dados brutos (milhares de imagens JPEG e máscaras PNG) residem compactados em arquivos `.zip` de alta taxa de compressão dentro de cada pasta de dataset.
* **Documentação `README.md` Descompactada e Individual:** Cada pasta de dataset possui seu próprio arquivo `README.md` contendo:
  1. *Site de Download Oficial e Links Diretos*
  2. *Data de Publicação / Atualização*
  3. *Quantidade Exata de Arquivos e Tamanho do Pacote*
  4. *Distribuição dos Dados (Splits de Treino/Validação/Teste e Proporções)*
  5. *Tipos de Arquivos e Classes Mapeadas*
  6. *Script de Descompactação Rápida sob Demanda*

---

### 1.3 Padrão dos Modelos de Deep Learning

O diretório `models/` é dividido em **3 categorias funcionais**:
1. **`01_satellite_and_aerial_naval/`:** Modelos de detecção em sensoriamento remoto (ex: `SixOpen_Y8NavalONNX` com 50 classes navais em fotos submétricas).
2. **`02_sar_radar_and_edge/`:** Modelos leves para dispositivos de borda, radares SAR e segmentação fluvial (`MeWan2808_YOLOv8_SAR`, `mayrajeo_YOLOv8_Marine_Vessel`, `beaunix_River_Segmentation`).
3. **`03_vessel_transformers/`:** Transformadores visuais de alta precisão (ex: `dima806_ViT_Vessel_Classification` baseado em auto-atenção).

Cada modelo inclui seus **pesos (`.onnx`, `.safetensors`, `.pt`)**, arquivos de configuração (`config.json`, `preprocessor_config.json`), imagens de teste em `examples/` e um `README.md` local com instruções de inferência.

---

### 1.4 Repositório Consolidado de Arquivos Compactados (`datasets/archives/`)

O diretório [`datasets/archives/`](./datasets/archives/) centraliza uma cópia de backup de todos os pacotes `.zip` do repositório, permitindo que um pesquisador ou engenheiro exporte todos os conjuntos de dados com um único comando de cópia.

---

## 📦 Tabela Mestra de Datasets

| Categoria / Dataset | Para que serve | Qual a Vantagem | Distribuição / Splits | Tipos de Arquivos | Qtd. Arquivos / Tamanho | Site de Download / Link Oficial | Atualização | Caminho Local |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01. LaRS** | Segmentação panóptica de obstáculos, calha d'água e céu | Padrão ouro mundial (#1 Bifrost); unifica rios, lagos e mar aberto | `train` (65.0% - 2.605 imgs)<br>`val` (5.0% - 198 imgs)<br>`test` (30.0% - 1.203 imgs) | `.jpg` (RGB HD)<br>`.png` (máscaras)<br>`.json` (COCO) | **9.643 arquivos**<br>Imagens: `966.29 MB`<br>Anotações: `22.36 MB` | [ViCoS LaRS Portal](https://lojzezust.github.io/lars-dataset/) | Out/2023 (v1.0) | [`datasets/01_panoptic_and_multimodal/LaRS/`](./datasets/01_panoptic_and_multimodal/LaRS/) |
| **01. SEANet** | Segurança marítima crítica: homem ao mar (`MOB`), destroços e gelo | Foco exclusivo em situações de salvamento e colisão em alto-mar | 488 imagens de treino com anotações COCO panópticas | `.jpg` (RGB HD)<br>`.json` (COCO) | **506 arquivos**<br>ZIP: `22.35 MB` | [Hugging Face SEANet](https://huggingface.co/datasets/SEA-AI/SEANet) | 2024 | [`datasets/01_panoptic_and_multimodal/SEANet_SEA_AI/`](./datasets/01_panoptic_and_multimodal/SEANet_SEA_AI/) |
| **01. WaterScenes** | Percepção multimodal e fusão Câmera RGB + Radar 4D Imaging + LiDAR | Radar 4D com elevação vertical e Doppler sob chuva e noite | 54.120 frames com nuvens de pontos 4D e anotações 2D/3D | `.pcd` (Radar 4D)<br>`.jpg` (RGB)<br>`.py` (DevKit) | **7 arquivos (DevKit)**<br>ZIP: `0.01 MB` | [WaterScenes GitHub](https://github.com/WaterScenes/WaterScenes) | 2025 | [`datasets/01_panoptic_and_multimodal/WaterScenes_4DRadar/`](./datasets/01_panoptic_and_multimodal/WaterScenes_4DRadar/) |
| **02. IWHR Floater V1** | Detecção de troncos, lixo plástico e detritos flutuantes em rios | Fotos fluviais reais com correnteza e turbidez; rótulos YOLO prontos | `train` (80.0% - 1.200 imgs)<br>`val` (20.0% - 300 imgs) | `.jpg` (HD)<br>`.xml` (Pascal VOC)<br>`.txt` (YOLO)<br>`.yaml` | **4.506 arquivos**<br>ZIP YOLO: `971.25 MB`<br>ZIP Bruto: `969.86 MB` | [Nature / Figshare](https://doi.org/10.6084/m9.figshare.27376851.v1) | Jan/2025 | [`datasets/02_fluvial_and_inland_waterways/IWHR_Floater_V1/`](./datasets/02_fluvial_and_inland_waterways/IWHR_Floater_V1/) |
| **02. Elwha River** | Segmentação contínua da calha navegável, cascalho e margens | Máscaras de alta densidade semântica para prevenção de encalhe de USVs | Conjunto unificado de 1.508 amostras em 4 shards Parquet | `.parquet` (binário)<br>`.jpg`, `.png`, `.py` | **30 arquivos**<br>ZIP: `1.38 GB` | [Hugging Face Datasets](https://huggingface.co/datasets/stodoran/elwha-segmentation-v1) | 2024 | [`datasets/02_fluvial_and_inland_waterways/Elwha_River_Segmentation/`](./datasets/02_fluvial_and_inland_waterways/Elwha_River_Segmentation/) |
| **02. WSODD** | Detecção de 14 categorias de alvos em superfícies aquáticas fluviais | Ampla variedade de reflexos solares e perturbações na água | 7.467 imagens com 21.911 instâncias anotadas | `.xml` (Pascal VOC)<br>`.py` (conversor) | Conversor VOC2COCO incluso | [WSODD GitHub](https://github.com/sunjiaen/WSODD) | 2022 | [`datasets/02_fluvial_and_inland_waterways/WSODD_Water_Surface/`](./datasets/02_fluvial_and_inland_waterways/WSODD_Water_Surface/) |
| **03. MaSTRe1325** | Segmentação semântica costeira (Mar, Céu e Terra) para USVs leves | Inclui telemetria de sensores inerciais (IMU pitch/roll) sincronizada | 1.325 frames de resolução 512x384 | `.png` (máscaras)<br>`.jpg` (imagens)<br>`.mat` (IMU) | **2.650 arquivos**<br>Máscaras: `1.97 MB`<br>Imagens: `21.12 MB`<br>IMU: `0.52 MB` | [ViCoS MaSTRe1325](https://box.vicos.si/borja/viamaro/index.html#mastr1325) | 2021 | [`datasets/03_coastal_and_stereo_usv/MaSTRe1325/`](./datasets/03_coastal_and_stereo_usv/MaSTRe1325/) |
| **03. MODD2** | Detecção estereoscópica de obstáculos e borda da água (*water-edge*) | Pares estéreo calibrados com máscaras de auto-oclusão do próprio USV | 28 sequências contínuas de vídeo estéreo com ground-truth | `.mat` (polígonos)<br>`.txt` (GPS)<br>`.png` (USV masks) | **17.550 arquivos**<br>Anotações: `5.73 MB`<br>GPS: `1.12 MB` | [ViCoS MODD2 Portal](https://box.vicos.si/borja/viamaro/index.html#modd2) | 2020 (v2) | [`datasets/03_coastal_and_stereo_usv/MODD2_Stereo/`](./datasets/03_coastal_and_stereo_usv/MODD2_Stereo/) |
| **04. SAR Ship Detection** | Detecção de navios e alvos marítimos em imagens de radar SAR | Imagens de radar penetram nuvens, chuva intensa e escuridão total | 1.160 pares de imagens e anotações JSON estruturadas | `.jpg` (radar SAR)<br>`.json` (bounding boxes) | **2.320 arquivos**<br>ZIP: `87.70 MB` | [Hugging Face SAR](https://huggingface.co/datasets/agungpambudi/sar-ship-detection) | 2025 | [`datasets/04_thermal_and_offshore/SAR_Ship_Detection/`](./datasets/04_thermal_and_offshore/SAR_Ship_Detection/) |
| **04. MassMIND** | Segmentação termográfica infravermelha de onda longa (LWIR 8-14 µm) | Navegação noturna, sob nevoeiro denso ou luz solar ofuscante | 2.944 imagens térmicas com 6 classes anotadas | `.png` (térmico 16-bit)<br>`.json` (máscaras) | Especificações e classes | [MassMIND GitHub](https://github.com/uml-marine-robotics/MassMIND) | 2024 | [`datasets/04_thermal_and_offshore/MassMIND_Thermal_LWIR/`](./datasets/04_thermal_and_offshore/MassMIND_Thermal_LWIR/) |
| **04. MARVEL 2016** | Reconhecimento e busca por similaridade de embarcações comerciais | Base massiva de 2 milhões de imagens com número IMO indexado | 2M de imagens divididas em splits de treino, teste e validação | `.dat` (atributos)<br>`.mat` (dados)<br>`.py` | Downloader oficial incluso | [MARVEL GitHub](https://github.com/avaapm/marveldataset2016) | 2021 | [`datasets/04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval/`](./datasets/04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval/) |
| **04. KOLOMVERSE** | Detecção de parques eólicos offshore, faróis e plataformas em 4K UHD | Foco em infraestruturas marítimas de alto-mar e zonas econômicas | Milhares de imagens 4K com anotações COCO | `.jpg` (4K UHD)<br>`.json` (COCO) | Especificações offshore | [KOLOMVERSE GitHub](https://github.com/MaritimeDataset/KOLOMVERSE) | 2023 | [`datasets/04_thermal_and_offshore/KOLOMVERSE_Offshore_4K/`](./datasets/04_thermal_and_offshore/KOLOMVERSE_Offshore_4K/) |
| **05. Roboflow Naval** | 10 Datasets de alvos navais, drones (UAV), infravermelho (NIR) e portos | Configurações prontas para treinamento imediato com YOLOv8/v9/v11 | 10 conjuntos com arquivos `data.yaml` individuais e catálogo | `.yaml` (classes)<br>`.json` (catálogo)<br>`.py` | **7 arquivos**<br>ZIP: `4.05 KB` | [Roboflow Universe](https://universe.roboflow.com) | Ago/2026 | [`datasets/05_roboflow_universe_catalog/`](./datasets/05_roboflow_universe_catalog/) |

---

## 🧠 Tabela Mestra de Modelos de Deep Learning

| Categoria / Modelo | Para que serve | Qual a Vantagem | Distribuição e Tipos de Arquivos | Tamanho | Site de Download / Repositório | Atualização | Caminho Local |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01. SixOpen Y8NavalONNX** | Detecção de **50 classes navais** (militares e civis) em fotos de satélite submétricas e aéreas | Abrange alvos militares detalhados em fotos submétricas de satélite | `Y8Naval.onnx`, `config.json` (50 classes), `preprocessor_config.json`, `examples/` | `100.98 MB` | [Hugging Face Y8NavalONNX](https://huggingface.co/SixOpen/Y8NavalONNX) | 2025 | [`models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/`](./models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/) |
| **02. MeWan2808 YOLOv8 SAR Vessel** | Detecção ultra-rápida (**38 ms** em CPU) de embarcações em radar SAR e neblina | Tempo de inferência de **38 ms** em CPU; ideal para dispositivos embarcados | `quantized/best.onnx`, `unquantized/best.pt`, CSV e JSON de métricas | `11.70 MB` | [Hugging Face MeWan2808](https://huggingface.co/MeWan2808) | 2025 | [`models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR/`](./models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR/) |
| **02. mayrajeo YOLOv8 Marine Vessel** | Detecção em tempo real de embarcações marítimas (lanchas, navios, botes e boias) | Modelo YOLOv8n ultra-leve otimizado para câmeras de bordo e costeiras | `YOLOv8n/yolov8n.pt`, `YOLOv8n/args.yaml` | `5.95 MB` | [Hugging Face mayrajeo](https://huggingface.co/mayrajeo/marine-vessel-detection-yolov8) | 2024 | [`models/02_sar_radar_and_edge/mayrajeo_YOLOv8_Marine_Vessel/`](./models/02_sar_radar_and_edge/mayrajeo_YOLOv8_Marine_Vessel/) |
| **02. beaunix River Segmentation** | Segmentação semântica de leito fluvial e superfície de água doce | Identificação precisa de calhas de rios e margens em imagens aéreas/terrestres | `best_model.pt` (PyTorch Checkpoint) | `104.49 MB` | [Hugging Face beaunix](https://huggingface.co/beaunix/river-segmentation) | 2024 | [`models/02_sar_radar_and_edge/beaunix_River_Segmentation/`](./models/02_sar_radar_and_edge/beaunix_River_Segmentation/) |
| **03. dima806 ViT Vessel Classifier** | Classificação de navios em 5 superclasses (`Cargo`, `Carrier`, `Cruise`, `Military`, `Tankers`) | Mecanismo de auto-atenção visual com alta robustez a variações de escala e oclusões | `model.safetensors`, `config.json`, `preprocessor_config.json` | `327.33 MB` | [Hugging Face dima806](https://huggingface.co/dima806/vessel_classification) | 2024 | [`models/03_vessel_transformers/dima806_ViT_Vessel_Classification/`](./models/03_vessel_transformers/dima806_ViT_Vessel_Classification/) |

---

## 🏆 Tabela Comparativa dos 14 Benchmarks Marítimos (Critérios Bifrost)

| # | Dataset | Ano | Sensores | Tarefa Principal | Ontologia | Diversidade | Rótulos | Total | Status Local |
| :-: | :--- | :-: | :--- | :--- | :-: | :-: | :-: | :-: | :--- |
| **1** | **LaRS** | 2023 | RGB Monocular | Segmentação Panóptica | ⭐⭐⭐⭐ (4) | ⭐⭐⭐⭐⭐ (5) | ⭐⭐⭐⭐ (4) | **13 / 15** | `01_panoptic_and_multimodal/LaRS/` |
| **2** | **WaterScenes** | 2024 | RGB + Radar 4D + LiDAR + IMU | Percepção Multimodal USV | ⭐⭐⭐⭐ (4) | ⭐⭐⭐⭐ (4) | ⭐⭐⭐⭐ (4) | **12 / 15** | `01_panoptic_and_multimodal/WaterScenes_4DRadar/` |
| **3** | **MODD2** | 2018 | Estéreo RGB + IMU/GPS | Detecção Estéreo e Borda da Água | ⭐⭐⭐ (3) | ⭐⭐⭐ (3) | ⭐⭐⭐⭐ (4) | **10 / 15** | `03_coastal_and_stereo_usv/MODD2_Stereo/` |
| **4** | **MaSTRe1325** | 2019 | RGB Monocular + IMU/GPS | Segmentação Semântica Costeira | ⭐⭐⭐⭐ (4) | ⭐⭐⭐ (3) | ⭐⭐⭐ (3) | **10 / 15** | `03_coastal_and_stereo_usv/MaSTRe1325/` |
| **5** | **SPSCD** | 2023 | Câmeras Ópticas HD | Monitoramento Portuário | ⭐⭐⭐ (3) | ⭐⭐⭐⭐ (4) | ⭐⭐⭐ (3) | **10 / 15** | Mapeado no manifesto |
| **6** | **KOLOMVERSE** | 2022 | Câmeras Ópticas 4K | Detecção em Águas Territoriais | ⭐⭐ (2) | ⭐⭐⭐⭐ (4) | ⭐⭐⭐⭐ (4) | **10 / 15** | `04_thermal_and_offshore/KOLOMVERSE_Offshore_4K/` |
| **7** | **Pohang Canal** | 2023 | LiDAR 3D + Radar + IR + Estéreo | Navegação em Águas Restritas | ⭐⭐⭐ (3) | ⭐⭐ (2) | ⭐⭐⭐⭐⭐ (5) | **10 / 15** | Mapeado no manifesto |
| **8** | **SMD (Singapore)** | 2017 | Câmeras Fixas/Móveis + NIR | Rastreamento Marítimo Geral | ⭐⭐⭐ (3) | ⭐⭐ (2) | ⭐⭐⭐⭐ (4) | **9 / 15** | Mapeado no manifesto |
| **9** | **SeaShips (MCVWT)** | 2018 | Câmeras Costeiras 1080p | Classificação Fina de Tráfego | ⭐⭐⭐ (3) | ⭐⭐ (2) | ⭐⭐⭐⭐ (4) | **9 / 15** | `05_roboflow_universe_catalog/` |
| **10** | **MassMIND** | 2023 | Câmera Térmica LWIR | Segmentação Térmica em USV | ⭐⭐⭐ (3) | ⭐⭐⭐ (3) | ⭐⭐⭐ (3) | **9 / 15** | `04_thermal_and_offshore/MassMIND_Thermal_LWIR/` |
| **11** | **MUSSID** | 2022 | Câmeras RGB 1080p | Detecção da Linha do Horizonte | ⭐⭐⭐ (3) | ⭐⭐⭐ (3) | ⭐⭐⭐ (3) | **9 / 15** | Mapeado no manifesto |
| **12** | **MARVEL 2016** | 2016 | Fotos Web (2 Milhões) | Classificação em Grande Escala | ⭐⭐ (2) | ⭐⭐ (2) | ⭐⭐⭐⭐ (4) | **8 / 15** | `04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval/` |
| **13** | **MariShipSegHEU**| 2020 | Câmeras Visíveis | Segmentação de Instâncias | ⭐⭐ (2) | ⭐⭐ (2) | ⭐⭐⭐⭐ (4) | **8 / 15** | Mapeado no manifesto |
| **14** | **VAIS** | 2023 | Visível + Térmico | Detecção Bimodal de Navios | ⭐⭐ (2) | ⭐⭐ (2) | ⭐⭐ (2) | **6 / 15** | Mapeado no manifesto |

---

## 📁 Árvore Completa de Diretórios do Projeto

```
goofy-raman/
├── README.md                                  # Guia Geral Master Consolidado
├── models/
│   ├── 01_satellite_and_aerial_naval/         # Sensoriamento Remoto & Fotos Orbitais
│   │   └── SixOpen_Y8NavalONNX/
│   │       ├── README.md                      # Documentação do modelo
│   │       ├── Y8Naval.onnx                   # Pesos ONNX (100.98 MB)
│   │       ├── config.json                    # Mapeamento das 50 classes
│   │       └── examples/                      # Imagens satelitais de teste
│   ├── 02_sar_radar_and_edge/                 # Radar SAR & Processamento de Borda
│   │   ├── MeWan2808_YOLOv8_SAR/              # YOLOv8n SAR Quantizado (38 ms)
│   │   │   ├── README.md
│   │   │   ├── quantized/best.onnx
│   │   │   └── unquantized/best.pt
│   │   ├── mayrajeo_YOLOv8_Marine_Vessel/     # YOLOv8n Marine Vessel Detection
│   │   │   ├── README.md
│   │   │   └── YOLOv8n/yolov8n.pt
│   │   └── beaunix_River_Segmentation/        # PyTorch River Semantic Segmentation
│   │       ├── README.md
│   │       └── best_model.pt
│   └── 03_vessel_transformers/                # Transformadores Visuais
│       └── dima806_ViT_Vessel_Classification/
│           ├── README.md                      # Documentação do modelo
│           ├── model.safetensors              # Pesos Safetensors (327.33 MB)
│           └── config.json                    # Classes de embarcações
├── datasets/
│   ├── 01_panoptic_and_multimodal/            # Benchmarks Panópticos & Multimodais
│   │   ├── LaRS/
│   │   │   ├── README.md                      # Documentação do LaRS
│   │   │   ├── lars_v1.0.0_images.zip         # ZIP das imagens (966 MB)
│   │   │   ├── lars_v1.0.0_annotations.zip    # ZIP das anotações (22 MB)
│   │   │   └── LaRS_evaluator.zip             # ZIP do toolkit evaluator
│   │   ├── SEANet_SEA_AI/
│   │   │   ├── README.md                      # Documentação do SEANet
│   │   │   └── SEANet_panoptic_dataset.zip    # ZIP do dataset panóptico (22.35 MB)
│   │   └── WaterScenes_4DRadar/
│   │       ├── README.md                      # Documentação do WaterScenes
│   │       └── WaterScenes_DevKit.zip         # ZIP do DevKit Python (0.01 MB)
│   ├── 02_fluvial_and_inland_waterways/       # Hidrovias Interiores e Rios
│   │   ├── fluvial_manifest.json              # Manifesto dos 10 datasets fluviais
│   │   ├── IWHR_Floater_V1/
│   │   │   ├── README.md                      # Documentação do IWHR Floater
│   │   │   ├── data.yaml                      # Configuração YOLO
│   │   │   ├── IWHR_Floater_V1_yolo.zip       # ZIP do dataset YOLO (971 MB)
│   │   │   └── IWHR_AI_Lable_Floater_V1-package1.zip # ZIP original (969 MB)
│   │   ├── Elwha_River_Segmentation/
│   │   │   ├── README.md                      # Documentação do Elwha
│   │   │   └── Elwha_river_segmentation.zip   # ZIP do dataset Parquet (1.38 GB)
│   │   └── WSODD_Water_Surface/
│   │       ├── README.md                      # Documentação do WSODD
│   │       └── VOC2COCO.py                    # Script de conversão
│   ├── 03_coastal_and_stereo_usv/             # Visão Costeira e Estereoscopia
│   │   ├── MaSTRe1325/
│   │   │   ├── README.md                      # Documentação do MaSTRe1325
│   │   │   ├── MaSTr1325_masks_512x384.zip    # ZIP das máscaras (1.97 MB)
│   │   │   ├── MaSTr1325_images_512x384.zip   # ZIP das imagens (21.12 MB)
│   │   │   └── MaSTr1325_imus_512x384.zip     # ZIP da telemetria IMU (0.52 MB)
│   │   └── MODD2_Stereo/
│   │       ├── README.md                      # Documentação do MODD2
│   │       ├── MODD2_annotations_v2.zip      # ZIP das anotações (5.73 MB)
│   │       ├── MODD2_GPS_data.zip             # ZIP dos dados GPS (1.12 MB)
│   │       └── MODD2_USVparts_masks.zip       # ZIP das máscaras de USV (4 KB)
│   ├── 04_thermal_and_offshore/               # Térmicos, Radar SAR e Estruturas Offshore
│   │   ├── SAR_Ship_Detection/                # Radar SAR Ship Detection (2.320 arquivos)
│   │   │   ├── README.md
│   │   │   └── sar_ship_detection.zip
│   │   ├── MassMIND_Thermal_LWIR/
│   │   │   └── README.md
│   │   ├── KOLOMVERSE_Offshore_4K/
│   │   │   └── README.md
│   │   └── MARVEL_2016_Vessel_Retrieval/
│   │       ├── README.md
│   │       └── MARVEL_Download.py
│   ├── 05_roboflow_universe_catalog/          # 10 Datasets do Roboflow Universe
│   │   ├── README.md                          # Documentação do Roboflow
│   │   ├── roboflow_manifest.json             # Catálogo de 10 datasets
│   │   ├── roboflow_naval_configs.zip         # ZIP de configurações de treino (4.05 KB)
│   │   └── configs/                           # Arquivos YAML individuais
│   ├── benchmarks_manifest/
│   │   └── bifrost_maritime_manifest.json     # Manifesto dos 14 benchmarks Bifrost
│   └── archives/                              # Cópia consolidada de todos os arquivos .zip
│       ├── lars_v1.0.0_images.zip
│       ├── lars_v1.0.0_annotations.zip
│       ├── LaRS_evaluator.zip
│       ├── SEANet_panoptic_dataset.zip
│       ├── Elwha_river_segmentation.zip
│       ├── IWHR_Floater_V1_yolo.zip
│       ├── IWHR_AI_Lable_Floater_V1-package1.zip
│       ├── MaSTr1325_masks_512x384.zip
│       ├── MaSTr1325_images_512x384.zip
│       ├── MaSTr1325_imus_512x384.zip
│       ├── MODD2_annotations_v2.zip
│       ├── MODD2_GPS_data.zip
│       ├── MODD2_USVparts_masks.zip
│       ├── sar_ship_detection.zip
│       ├── roboflow_naval_configs.zip
│       └── WaterScenes_DevKit.zip
└── scripts/
    ├── run_y8naval_inference.py               # Inferência ONNX Naval Satélite (50 classes)
    ├── run_sar_vessel_inference.py            # Inferência ONNX SAR/Fluvial (38 ms)
    ├── download_sar_ship_fast.py              # Downloader multithread de datasets HF
    ├── download_roboflow_dataset.py           # Downloader de datasets do Roboflow Universe
    ├── generate_roboflow_configs.py           # Gerador de configs do Roboflow
    ├── setup_fluvial_devkits.py               # Integrador dos DevKits WaterScenes/WSODD
    ├── setup_benchmark_toolkits.py            # Setup dos benchmarks ViCoS
    ├── download_datasets.py                   # Gerenciador de downloads universal
    ├── reorganize_repository.py               # Reorganizador da hierarquia do repositório
    └── verify_environment.py                  # Script de validação de integridade
```

---

## 🚀 Guia de Execução, Treinamento e Inferência

### 1. Inferência com Modelo Naval Satelital (50 Classes)

```bash
python scripts/run_y8naval_inference.py --conf 0.15 --output resultado_naval.png
```

---

### 2. Inferência com Modelo SAR / Fluvial (Ultra-Rápido 38 ms)

```bash
python scripts/run_sar_vessel_inference.py --conf 0.20 --output resultado_sar.png
```

---

### 3. Rastreamento de Trajetória, ID Único e Vetor de Rumo (Heading)

Demonstração do pipeline completo de rastreamento com cálculo do ângulo de navegação (0°-360°) e esteira de trajetória:

```bash
python scripts/track_and_heading.py
```

---

### 4. Extração de Assinatura Visual Única e Re-Identificação (Vessel Re-ID)

Demonstração de extração de embeddings visuais de barcos via Vision Transformers e busca por similaridade de cosseno:

```bash
python scripts/vessel_reid_extractor.py
```

---

### 5. Verificação de Integridade Geral do Repositório

```bash
python scripts/verify_environment.py
```

---

## 🎯 Arquitetura de IA para Identificação, Re-ID Único e Análise de Trajetória de Barcos

Para o objetivo específico de **identificar embarcações**, **reconhecer unicamente cada barco (Re-ID)** e **analisar o vetor de rumo e trajetória (para onde estão indo)**, o repositório é articulado em 3 etapas integradas:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   PIPELINE COMPLETO DE INTELIGÊNCIA ARTIFICIAL AQUÁTICA                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: DETECÇÃO & LOCALIZAÇÃO EM TEMPO REAL                                                    │
│ Modelos: SixOpen_Y8NavalONNX, mayrajeo_YOLOv8, MeWan2808_YOLOv8_SAR                             │
│ Datasets: LaRS, IWHR_Floater_V1, Roboflow Suite (10 Datasets)                                    │
│ Função: Detectar caixas delimitadoras (bounding boxes) e classificar tipos de embarcações.       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: IDENTIFICAÇÃO ÚNICA & RE-IDENTIFICAÇÃO (Re-ID)                                          │
│ Modelos: dima806_ViT_Vessel_Classification (Vision Transformer)                                  │
│ Datasets: MARVEL 2016 (Mapeamento de IMO e Similaridade Fina de Instâncias)                      │
│ Função: Extrair embeddings de 768 dimensões para reconhecer o MESMO barco entre câmeras/pontos.  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: RASTREAMENTO MULTI-OBJETO, VETORES DE CURSO & TRAJETÓRIA                                │
│ Modelos & Scripts: ByteTrack / BoT-SORT + scripts/track_and_heading.py                           │
│ Datasets: WaterScenes 4D (Velocidade Doppler/Radar 4D), MODD2 Stereo (Distância Métrica)         │
│ Função: Rastrear histórico temporal, calcular vetor de deslocamento (dx, dy) e rumo (0°-360°).   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```


# 📐 Arquitetura do Sistema e Pipeline Multi-Domínio

Este documento detalha o design técnico, a estrutura de camadas, os módulos de visão computacional e o fluxo de dados da plataforma.

---

## 1. Visão Geral da Arquitetura

O sistema é construído sobre uma arquitetura em camadas modular e fracamente acoplada:

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Camada de Apresentação                         │
│  - Web CVAT Studio (HTML5/Canvas 2D / JS Assíncrono)                  │
│  - Desktop GUI (Tkinter + PIL + OpenCV)                               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST / WebSocket
┌───────────────────────────────────▼────────────────────────────────────┐
│                        Camada de Serviços (Flask)                      │
│  - /api/annotation/* (Auto-Detect, Save, Load, Import/Export ZIP)     │
│  - /api/class_sets/* (Gestão de Conjuntos de Classes)                 │
│  - /api/architectures/* (Alternância de Arquiteturas)                 │
│  - /api/benchmark/* (Medição Comparativa de Latência e Throughput)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                       Pluggable Vision Pipeline                        │
│  - ModelRegistry (Escaneamento e Inicialização Dinâmica de Pesos)     │
│  - Ultralytics YOLOv8 / YOLO11 / ONNX Runtime Inferences             │
│  - Non-Maximum Suppression (NMS) & Intersection over Union (IoU)      │
│  - Multi-Model Ensemble Consensus Engine                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                     Camada de Domínios Especialistas                   │
│  - 7 Analisadores de Domínio (Naval, Urbano, Fechado, Natureza, etc.) │
│  - Vision Transformer (ViT-Base 768D) Embedding Extractor             │
│  - Base de Dados Vetorial & Re-Identificação (Cosine / FAISS)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                 Camada de Persistência & Datasets                      │
│  - DatasetAnnotationManager (Estrutura YOLO: images/ e labels/)        │
│  - Active Learning Manifest (manifest.json com flag de correção)      │
│  - Class Preset Configs (configs/classes_presets.json)                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pluggable Vision Pipeline (`src/pipeline/pluggable_pipeline.py`)

O pipeline suporta carregar múltiplos modelos simultaneamente e rotear a inferência com base no `active_model_id` ou em modo ensemble:

1. **`ModelRegistry`**:
   - Varre o diretório `models/` e identifica modelos nos formatos `.pt`, `.onnx`, `.engine`, `.safetensors`.
   - Gera um catálogo unificado contendo ID, nome, framework, resolução de entrada, classes e confiança padrão.

2. **Modos de Inferência**:
   - `single_model`: Roda inferência ultrarrápida usando um único detector (ex: YOLO11n para edge).
   - `ensemble`: Roda múltiplos detectores em paralelo e unifica caixas usando IoU weighted box fusion.

---

## 3. Vetorização e Re-ID com Vision Transformer

Para rastreamento e reconhecimento contínuo de objetos:
- O módulo recorta a região de interesse (ROI) do alvo detectado.
- Redimensiona e normaliza para entrada no **ViT-Base (224x224)**.
- Extrai um vetor de características denso de **768 dimensões**.
- Calcula a similaridade por cosseno contra a base de registros conhecidos:
  - Se $	ext{Similaridade} \ge 0.72$, classifica como **Re-Identificado**.
  - Se $	ext{Similaridade} < 0.72$, executa **Auto-Cadastro** do novo alvo.

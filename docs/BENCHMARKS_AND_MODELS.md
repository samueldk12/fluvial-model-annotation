# 📊 Catálogo de Modelos e Relatório de Benchmarks

Este documento apresenta os resultados comparativos de latência, consumo de memória e desempenho entre as arquiteturas suportadas.

---

## 1. Comparativo de Arquiteturas

| Métrica | Pré-Arquitetura (Produção Multi-Modelo) | Nova Arquitetura de Teste (YOLO11n Edge) |
| :--- | :--- | :--- |
| **Pipeline** | Ensemble (3 YOLO + eWaSR + ViT + OCR) | YOLO11n Single-Pass |
| **Latência por Frame** | 618.4 ms | 55.1 ms |
| **Throughput** | ~1.6 FPS | ~18.1 FPS |
| **Speedup Relativo** | 1.0x (Referência) | **11.22x mais rápida** ⚡ |
| **Consumo de Memória VRAM** | ~2.8 GB | ~420 MB |
| **Ambiente de Destino** | Servidores Centrais / Análise Forense | Drones, USVs, Câmeras Inteligentes |

---

## 2. Catálogo de Modelos Integrados

### 1. `yolo11n` (YOLO11 Nano Baseline)
- **Framework**: Ultralytics PyTorch / ONNX
- **Tamanho do Peso**: ~5.6 MB
- **Resolução Padrão**: 640x640
- **Uso Recomendado**: Detecção rápida em edge e auto-rotulagem interativa.

### 2. `mayrajeo_marine` (YOLOv8 Marine Vessel)
- **Framework**: PyTorch
- **Tamanho do Peso**: ~12.4 MB
- **Uso Recomendado**: Detecção naval específica em rios e costas.

### 3. `mewan2808_sar` (YOLOv8 SAR Radar Ship)
- **Framework**: PyTorch
- **Uso Recomendado**: Sensoriamento por Radar de Abertura Sintética (SAR) para visão através de nuvens e névoa.

### 4. `sixopen_y8naval` (SixOpen Y8Naval)
- **Framework**: ONNX Runtime
- **Uso Recomendado**: Imagens aéreas de alta altitude e fotos submétricas de satélite (50 classes navais).

### 5. `ensemble_full` (Ensemble Multi-Domínio)
- **Framework**: PyTorch + ONNX Híbrido
- **Uso Recomendado**: Máxima precisão e consenso com filtragem de falsos positivos.

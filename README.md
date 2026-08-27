# 🌊 Sistema de Visão Computacional Multi-Domínio & Estúdio de Anotação com Active Learning

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange.svg)](https://pytorch.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8%20%7C%2011%20%7C%2026-green.svg)](https://github.com/ultralytics/ultralytics)
[![Tests](https://img.shields.io/badge/Tests-28%2F28%20Passing%20(100%25)-brightgreen.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Multi--Domain%20%26%20Pluggable-blueviolet.svg)](docs/ARCHITECTURE.md)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

Plataforma avançada de **Visão Computacional**, **Percepção Semântica**, **Identificação Biométrica/Cargas/Re-ID** e **Estúdio de Anotação Assistida por IA (Human-in-the-Loop)** com suporte a 7 domínios operacionais e arquitetura plugável de modelos de Deep Learning.

---

## 📌 Sumário
1. [🌟 Destaques e Principais Funcionalidades](#-destaques-e-principais-funcionalidades)
2. [🏗️ Arquitetura do Sistema](#️-arquitetura-do-sistema)
3. [🎯 Os 7 Domínios Especialistas](#-os-7-domínios-especialistas)
4. [🤖 Estúdio de Anotação Web & Active Learning (Human-in-the-Loop)](#-estúdio-de-anotação-web--active-learning-human-in-the-loop)
5. [🖥️ Interface Gráfica Desktop (Tkinter)](#️-interface-gráfica-desktop-tkinter)
6. [📊 Benchmarks Comparativos de Desempenho](#-benchmarks-comparativos-de-desempenho)
7. [🌐 Documentação da API REST (Flask)](#-documentação-da-api-rest-flask)
8. [🧪 Suíte de Testes Automatizados (28/28 Pass)](#-suíte-de-testes-automatizados-2828-pass)
9. [🚀 Guia de Instalação e Execução](#-guia-de-instalação-e-execução)
10. [📚 Documentação Técnica Aprofundada](#-documentação-técnica-aprofundada)

---

## 🌟 Destaques e Principais Funcionalidades

- **🤖 Modelos de IA Acopláveis (Pluggable AI Models)**:
  - Catálogo integrado com suporte dinâmico a múltiplos detectores: **YOLO11n**, **YOLOv8 Marine Vessel**, **MeWan2808 SAR Radar**, **SixOpen Y8Naval (Aéreo/Satélite)**, **eWaSR ResNet18 (Segmentação de Água)** e **Ensemble Multi-Domínio**.
  - Permite alternar modelos em tempo de execução sem reiniciar o servidor.

- **✏️ Estúdio de Anotação com Modelo Atrelado & Active Learning**:
  - **Detecção Automática ao Pausar**: Ao pausar o vídeo ou congelar a câmera ao vivo, a IA gera automaticamente caixas delimitadoras no frame atual.
  - **Edição Interativa no Canvas**: Clique e arraste para reposicionar caixas delimitadoras, redimensione usando as alças dos 4 cantos (`nw`, `ne`, `se`, `sw`) e troque a classe instantaneamente via atalhos numéricos (`1 a 9`).
  - **🗑️ Deletar Todas as Anotações**: Botão de 1 clique (`Alt+C`) para limpar previsões incorretas da IA e refazer do zero.
  - **💾 Salvamento de Ground Truth**: Gravação com metadados de auxílio de IA (`is_ai_assisted=True`, `model_used`, `human_corrected=True`) no formato YOLO para evolução contínua dos modelos.

- **🧠 Memória Visual Vetorial & Re-ID**:
  - Extração de embeddings de 768 dimensões com **Vision Transformer (ViT-Base)**.
  - Reconhecimento e re-identificação biométrica e cadastral (embarcações, veículos, animais, impressões digitais, etc.) com similaridade por cosseno / FAISS.

- **⚡ Benchmarking e Comparação de Arquiteturas**:
  - Módulo integrado para comparar em tempo real a **Pré-Arquitetura de Produção (Ensemble Multi-Modelo)** contra a **Nova Arquitetura de Teste (YOLO11n Edge)**, com ganho medido de **11.22x mais velocidade**.

---

## 🏗️ Arquitetura do Sistema

```
                                  ┌───────────────────────────────────┐
                                  │      Plataforma Multi-Domínio     │
                                  │       (Web CVAT + GUI Desktop)    │
                                  └─────────────────┬─────────────────┘
                                                    │
                 ┌──────────────────────────────────┼──────────────────────────────────┐
                 │                                  │                                  │
   ┌─────────────▼─────────────┐      ┌─────────────▼─────────────┐      ┌─────────────▼─────────────┐
   │    Pluggable Pipeline     │      │   Active Learning Studio  │      │  Multi-Domain Analyzers   │
   │  - ModelRegistry          │      │  - Video Player & Pause   │      │  - 7 Domínios Isolados    │
   │  - YOLOv8 / YOLO11 / ONNX │      │  - Interactive Canvas BBox│      │  - ViT 768D Embeddings    │
   │  - Multi-Model Ensemble   │      │  - Delete All / 1-Click   │      │  - Vector Re-ID Registry  │
   │  - Dynamic Weight Loader  │      │  - YOLO Dataset Exporter  │      │  - Domain Presets / YAML  │
   └───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

---

## 🎯 Os 7 Domínios Especialistas

Cada domínio possui analisadores semânticos dedicados, modelos otimizados, base de dados vetorial isolada e conjunto de classes customizável:

| Domínio | Rota Web | Alvos & Foco Operacional |
| :--- | :--- | :--- |
| 🌊 **Naval** | `/naval` / `/` | Embarcações, cargueiros, rebocadores, boias, superfície d'água, calado e rumo náutico |
| 🏙️ **Urbano** | `/urbano` | Veículos, carros, ônibus, caminhões, motos, pedestres e placas de trânsito |
| 🏢 **Fechado** | `/fechado` | Ambientes internos, escritórios, móveis, EPIs, segurança patrimonial e pessoas |
| 🌿 **Natureza** | `/natureza` | Animais silvestres, aves, vegetação, monitoramento ambiental e corpos hídricos |
| 📦 **Objetos** | `/objetos` | Peças industriais, ferramentas, embalagens, caixas, contêineres e controle de estoque |
| 🎨 **Tatuagens** | `/tatuagens` | Identificação biométrica forense, estilos artísticos, símbolos e localização corporal |
| 🔍 **Digitais** | `/digitais` | Papiloscopia, minúcias datiloscópicas, arcos, presilhas e verificação biométrica |

---

## 🤖 Estúdio de Anotação Web & Active Learning (Human-in-the-Loop)

Acesse em: `http://localhost:5000/anotar` (ou `/anotar/urbano`, `/anotar/natureza`, etc.).

### Fluxo de Trabalho
1. **Carregar Mídia**: Selecione um vídeo gravado (`.mp4`) ou transmissão de câmera ao vivo (`RTSP / WebRTC`).
2. **Pausar no Frame**: Pressione <kbd>Espaço</kbd> ou avance com <kbd>D</kbd> / <kbd>F</kbd>.
3. **Predição Automática**: O modelo de IA atrelado gera instantaneamente as caixas delimitadoras.
4. **Correção Humana**:
   - Arraste a caixa para corrigir a posição.
   - Puxe os cantos para ajustar o tamanho exato.
   - Pressione <kbd>1 a 9</kbd> para trocar a classe.
   - Se a IA errou tudo, clique em `🗑️ Deletar Tudo` (<kbd>Alt+C</kbd>) e rotule do zero.
5. **Gravar no Dataset**: Pressione <kbd>Ctrl+S</kbd> para salvar a anotação YOLO corrigida e continuar a reprodução.
6. **Exportar**: Clique em `📦 Exportar` para baixar o dataset consolidado em `.ZIP` com `data.yaml` pronto para treinamento do YOLO.

### Atalhos de Teclado no Estúdio
- <kbd>Espaço</kbd>: Play / Pause ou Congelar / Retomar
- <kbd>A</kbd>: Executar inferência do modelo de IA atrelado no frame
- <kbd>Alt + C</kbd>: Deletar todas as anotações do frame
- <kbd>Ctrl + S</kbd>: Salvar frame corrigido no dataset
- <kbd>D</kbd> / <kbd>F</kbd>: Frame anterior / próximo
- <kbd>N</kbd> / <kbd>R</kbd>: Modo Retângulo (BBox)
- <kbd>P</kbd>: Modo Polígono (Segmentação)
- <kbd>1 a 9</kbd>: Alternar classe ativa

---

## 🖥️ Interface Gráfica Desktop (Tkinter)

Para operação offline e em estações de monitoramento sem navegador web:

```bash
python src/gui/app.py
```

- Seletor de modelo de IA atrelado (YOLO11, MeWan2808, SixOpen, Ensemble).
- Player de vídeo com avanço frame a frame.
- Canvas com desenho, arraste e redimensionamento interativo de caixas delimitadoras.
- Botões de execução rápida da IA, exclusão total e gravação de ground truth no dataset.

---

## 📊 Benchmarks Comparativos de Desempenho

| Métrica | Pré-Arquitetura (Produção Multi-Modelo) | Arquitetura de Teste (YOLO11n Edge) | Variação / Ganho |
| :--- | :--- | :--- | :--- |
| **Latência por Frame** | 618.4 ms | 55.1 ms | **11.22x mais rápida** ⚡ |
| **Throughput Estimado** | ~1.6 FPS | ~18.1 FPS | **+1031% FPS** |
| **Consumo de VRAM/RAM** | Alto (~2.8 GB) | Muito Baixo (~420 MB) | **-85% memória** |
| **Pipeline de Modelos** | 3 YOLO + eWaSR + ViT + OCR | YOLO11n Single-Pass | Otimizado para Edge |
| **Finalidade** | Alta Fidelidade & Forense | Edge, Drones e Câmeras Embarcadas | Flexibilidade Total |

---

## 🌐 Documentação da API REST (Flask)

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/api/annotation/models` | Lista todos os modelos de IA disponíveis para o domínio |
| `POST` | `/api/annotation/auto_detect` | Executa inferência do modelo selecionado no frame base64 |
| `POST` | `/api/annotation/save` | Salva anotação com metadados de Active Learning |
| `GET` | `/api/annotation/list` | Lista todos os frames salvos no dataset do domínio |
| `GET` | `/api/annotation/load/<image_id>` | Carrega imagem e caixas anotadas para revisão |
| `DELETE` | `/api/annotation/delete/<image_id>` | Exclui um frame anotado do dataset |
| `GET` | `/api/annotation/export_zip` | Exporta pacote ZIP do dataset com `data.yaml` |
| `POST` | `/api/annotation/import_zip` | Importa dataset existente em ZIP e retoma anotações |
| `GET` | `/api/class_sets` | Lista os conjuntos de classes cadastrados |
| `POST` | `/api/class_sets/save` | Cria e persiste novo conjunto de classes |
| `POST` | `/api/class_sets/set_active` | Ativa um conjunto de classes para a rotulagem |
| `GET` | `/api/architectures` | Retorna arquiteturas cadastradas e seus pipelines |
| `POST` | `/api/architectures/apply` | Alterna a arquitetura do pipeline em tempo real |
| `POST` | `/api/benchmark/run` | Executa benchmark comparativo de latência e precisão |

---

## 🧪 Suíte de Testes Automatizados (28/28 Pass)

Para rodar todos os testes unitários, de integração e de benchmarks:

```bash
python tests/run_all_automated_tests.py
```

```
================================================================================
                     RELATÓRIO FINAL DE VALIDAÇÃO
================================================================================
Total de Testes Executados: 28
Testes Aprovados (Pass):   28
Falhas (Failures):         0
Erros (Errors):            0
Tempo Total:               30.83 segundos

>>> SUCESSO: 100% DOS TESTES AUTOMATIZADOS PASSARAM COM ÊXITO! <<<
================================================================================
```

---

## 🚀 Guia de Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/samueldk12/fluvial-model-annotation.git
cd fluvial-model-annotation
```

### 2. Criar Ambiente Virtual e Instalar Dependências
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Iniciar o Servidor Web Multi-Domínio
```bash
python src/web/app.py
```
Acesse `http://localhost:5000` no navegador.

### 4. Iniciar a Interface Gráfica Desktop
```bash
python src/gui/app.py
```

---

## 📚 Documentação Técnica Aprofundada

- [📐 Arquitetura do Sistema e Pipeline Multi-Domínio](docs/ARCHITECTURE.md)
- [🤖 Guia de Anotação Interativa e Active Learning](docs/ACTIVE_LEARNING_ANNOTATION.md)
- [🌐 Referência Completa da API REST](docs/API_REFERENCE.md)
- [📊 Catálogo de Modelos e Relatório de Benchmarks](docs/BENCHMARKS_AND_MODELS.md)

---

## 📄 Licença
Distribuído sob a licença MIT. Consulte `LICENSE` para mais detalhes.

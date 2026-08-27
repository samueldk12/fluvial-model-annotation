# 🤖 Guia de Anotação Interativa e Active Learning (Human-in-the-Loop)

Este documento explica como utilizar o Estúdio de Anotação para gerar datasets de alta precisão com assistência de IA e refinamento humano contínuo.

---

## 1. O Conceito de Active Learning / Human-in-the-Loop

Treinar modelos de detecção de objetos do zero exige rotular milhares de imagens manualmente. O fluxo **Human-in-the-Loop** acelera esse processo em até 10x:

1. Um modelo pré-treinado ou intermediário realiza **predições iniciais** no frame.
2. O operador humano inspeciona as caixas geradas.
3. Se as caixas estiverem corretas ou levemente deslocadas, o operador apenas **ajusta o tamanho ou reposiciona**.
4. Se o modelo falhou completamente ou cometeu falso positivo, o operador clica em **Deletar Tudo** e anota manualmente.
5. O frame é gravado com metadados de validação e adicionado à fila de re-treinamento do modelo.

---

## 2. Interface de Anotação (Web CVAT)

### Controles no Topo (Header)
- **Seletor de Modelo de IA**: Escolha qual modelo executará a inferência prévia no frame.
- **⚡ Auto-IA: ON/OFF**: Habilita a detecção automática assim que o vídeo é pausado.
- **💾 Salvar (Ctrl+S)**: Grava a anotação atual no dataset YOLO e retoma o vídeo automaticamente.
- **🤖 Auto-IA (A)**: Dispara a inferência do modelo no frame atual sob demanda.
- **🗑️ Deletar Tudo (Alt+C)**: Remove todas as caixas delimitadoras e polígonos do frame atual.

### Edição no Canvas 2D
- **Mover Caixa**: Clique dentro do retângulo e arraste.
- **Redimensionar**: Clique e arraste qualquer uma das 4 alças azuis nos cantos da caixa.
- **Mudar Classe**: Selecione a caixa e pressione <kbd>1</kbd> a <kbd>9</kbd> no teclado.
- **Excluir Caixa Específica**: Selecione a caixa e pressione <kbd>Delete</kbd> ou <kbd>Backspace</kbd>.

---

## 3. Estrutura do Dataset Gerado

Ao salvar um frame, o `DatasetAnnotationManager` grava:

```
datasets/naval_yolo/
├── images/
│   ├── frame_1724773800_001.jpg
│   └── frame_1724773805_002.jpg
├── labels/
│   ├── frame_1724773800_001.txt
│   └── frame_1724773805_002.txt
├── manifest.json
└── data.yaml
```

### Formato do Label YOLO (`.txt`):
Cada linha segue o padrão oficial normalizado:
```
<class_id> <center_x> <center_y> <width> <height>
```

### Registro no `manifest.json`:
```json
{
  "frame_1724773800_001": {
    "filename": "frame_1724773800_001.jpg",
    "label_file": "frame_1724773800_001.txt",
    "timestamp": 1724773800.12,
    "num_boxes": 3,
    "is_ai_assisted": true,
    "model_used": "yolo11n",
    "human_corrected": true,
    "notes": "Anotação assistida por IA corrigida pelo operador."
  }
}
```

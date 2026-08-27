# 🌐 Referência Completa da API REST

A API Flask fornece endpoints RESTful para anotação, gerenciamento de modelos, benchmarks e controle de fluxos de vídeo.

---

## 1. Endpoints de Anotação & Modelos de IA

### `GET /api/annotation/models`
Retorna os modelos de IA disponíveis para o domínio especificado.
- **Query Params**: `domain` (opcional, padrão: `naval`)
- **Resposta**:
```json
{
  "status": "ok",
  "domain": "naval",
  "active_model_id": "yolo11n",
  "models": [
    {
      "id": "yolo11n",
      "name": "YOLO11n Baseline Edge",
      "framework": "PyTorch",
      "default_conf": 0.20
    }
  ]
}
```

---

### `POST /api/annotation/auto_detect`
Executa a inferência de um modelo de IA em uma imagem codificada em base64.
- **Body**:
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "model_id": "yolo11n",
  "conf": 0.20,
  "domain": "naval"
}
```
- **Resposta**:
```json
{
  "status": "ok",
  "model_id": "yolo11n",
  "model_used": "yolo11n",
  "domain": "naval",
  "conf_threshold": 0.20,
  "count": 2,
  "detections": [
    {
      "bbox": [120, 85, 340, 210],
      "class_id": 0,
      "class_name": "embarcacao",
      "confidence": 0.88,
      "source_model": "yolo11n"
    }
  ]
}
```

---

### `POST /api/annotation/save`
Salva o frame anotado com caixas delimitadoras e/ou polígonos no dataset YOLO.
- **Body**:
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "boxes": [{"x1": 100, "y1": 50, "x2": 250, "y2": 180, "class_id": 0, "class_name": "embarcacao"}],
  "polygons": [],
  "domain": "naval",
  "source_video": "camera_porto.mp4",
  "frame_timestamp": 14.2,
  "model_used": "yolo11n",
  "is_ai_assisted": true,
  "human_corrected": true
}
```
- **Resposta**:
```json
{
  "status": "ok",
  "image_id": "frame_1724773800_001",
  "filename": "frame_1724773800_001.jpg",
  "num_boxes": 1,
  "num_polygons": 0
}
```

---

### `GET /api/annotation/list`
Lista todos os frames anotados salvos no dataset.
- **Query Params**: `domain` (opcional)

---

### `GET /api/annotation/export_zip`
Gera e faz o download do dataset YOLO completo em formato `.zip` com `images/`, `labels/` e `data.yaml`.

---

### `POST /api/annotation/import_zip`
Importa um arquivo `.zip` contendo imagens e labels YOLO para retomar o trabalho de anotação.

---

## 2. Endpoints de Conjuntos de Classes

### `GET /api/class_sets`
Lista todos os presets de classes salvos.

### `POST /api/class_sets/save`
Salva um novo preset de classes personalizado.

### `POST /api/class_sets/set_active`
Define o preset ativo para rotulagem.

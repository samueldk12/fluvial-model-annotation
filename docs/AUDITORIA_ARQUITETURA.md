# Auditoria da Nova Arquitetura (AI Vision Hub multi-domínio)

Registro dos achados da revisão pedida em 2026-08-27, para referência futura.

## 🔴 CRÍTICO — Dados fabricados (CORRIGIDO nesta auditoria)

**`src/domains/domain_analyzer.py`** tinha três fontes de detecção fabricada:

1. `_fallback_domain_detections()` — quando o YOLO real não achava nada, inventava
   caixas fixas com confiança hardcoded (ex: "carro" a 91% sempre na mesma posição
   da tela) só pra a interface não ficar vazia. Testado ao vivo em produção:
   `/api/urbano/live_telemetry` retornou um "Automóvel Particular" com
   `status_reid: RE_IDENTIFICADO`, `sightings: 33`, posição fixa (320, 432) — um
   veículo inteiro com histórico fictício que nunca existiu.
2. `_detect_fingerprints()` — adicionava uma caixa de "impressão digital" a 99% de
   confiança **incondicionalmente**, para qualquer imagem, mais "minúcias" a partir
   de cantos genéricos (`goodFeaturesToTrack`), sem nenhuma verificação de que a
   imagem continha uma digital.
3. `_detect_tattoos()` — contorno/textura genérico (`adaptiveThreshold`) dispara em
   qualquer superfície texturizada; o rótulo "oriental" vs "blackwork" era só um
   limiar arbitrário de área de contorno, não reconhecimento de estilo real.
4. `_resolve_target_attributes()` — fabricava especificidade que nenhum modelo
   determinou: qualquer "car" virava "Sedan Médio / SUV", qualquer "bird" virava
   "Tucano/Gavião", "person" no domínio tatuagem virava "Arte Dérmica Vetorizada /
   Estilo Oriental / Blackwork".
5. `src/web/app.py` (2 lugares, linhas ~252 e ~558) — bug de precedência de
   operador (`A or B or C if D else C`) fazia qualquer embarcação sem OCR real
   mostrar `"IMO 9074729"` fixo, como se fosse um número real lido do casco.

**Correção aplicada:** removidas as três funções de fabricação; `_resolve_target_attributes`
reescrita pra usar só a classe real do detector (com tradução PT-BR, sem inventar
marca/modelo/espécie/estilo); o IMO fabricado virou `"Sem leitura de OCR"` honesto.
Efeito colateral: os domínios `tatuagens` e `digitais` agora reportam corretamente
"nada detectado" na maioria dos casos, porque não existe heurística confiável sem
um modelo dedicado — isso é o comportamento correto, não uma regressão.

**Segunda rodada (mesma auditoria):** achado adicional de fabricação em
`_extract_scene_semantics()` (`domain_analyzer.py`) — praticamente todo domínio
não-naval reportava métricas 100% inventadas como se fossem medidas reais:
`estado_semaforo`/`fluxo_pedestres` (urbano), `estado_portas`/`seguranca_indoor`
(fechado, com piso artificial `max(pessoas, 2)`), `alerta_ambiental` +
biodiversidade fake `len(detections)+3` (natureza), esteira/qualidade
100% hardcoded (objetos), e domínios inteiros tatuagens/digitais fabricados.
Reescrito pra reportar só o que é realmente medido (contagem real, cobertura de
cor real) e `"N/D (sem detector de X)"` honesto pro resto.

Também achado em `app.py` (rota de vídeo ao vivo E rota `/api/analyze_image`,
ambas com o mesmo bug duplicado): fallbacks fabricados quando o campo não vinha
do pipeline — `vessel_id` fixo "BR-STS-01", `destination` fixo "Canal de Santos",
`cardinal` fixo "Proa Fixa", `cor_casco` fixo "Cinza Naval / Escuro", `score`
fixo 85%, `latency_ms` fixo 18.5, e principalmente `cobertura_agua_pct: 78.5`
**nunca calculado, sempre o mesmo número**. Corrigido: todos os fallbacks agora
são "N/D"/0.0, e `cobertura_agua_pct` passou a vir de
`water_segmenter.water_coverage_pct()` sobre a máscara real da eWaSR (agora
guardada em `pluggable_pipeline.last_water_mask`).

Por fim, os valores "default" pré-carregamento em `domain_config.py`
(`semantics_keys`/`target_keys`, 49 ocorrências em 7 domínios) mostravam dados
fictícios específicos (ex: espécie "Cervo-do-Pantanal", hash biométrico
"7f8a9e2c...", score AFIS "98.7%") na primeira renderização da página, antes do
primeiro frame real chegar via polling JS. Trocados por "Aguardando dados..."
neutro. Verificado ao vivo: `curl http://127.0.0.1:5000/urbano` já não contém
nenhum dos textos fabricados antigos.

## 🟠 Regressões no pipeline naval (PENDENTE)

`src/pipeline/pluggable_pipeline.py` reimplementou a detecção sem usar mais
`vessel_ensemble_engine.py`, e no caminho perdeu 3 salvaguardas validadas nesta sessão:

- `night_frame` (visão noturna) é calculado em `process_frame()` mas **nunca
  usado** depois — o consenso dia/noite não roda mais.
- Score de Laplaciano (anti-reflexo) é calculado (`lap_score`) e guardado no dict
  de saída, mas **nunca comparado a um limiar** — não rejeita mais nada.
- `is_plausible_vessel_size` é importado no topo do arquivo mas **nunca chamado**
  — sem teto de tamanho contra caixas degeneradas/sprawling.
- `conf_threshold` default é 0.05, mais permissivo que qualquer valor validado
  nesta sessão (0.12–0.20), o que piora o impacto dos itens acima.

**Fix recomendado:** dentro de `process_frame()`, usar `night_frame` num segundo
passe de detecção quando `is_night_or_low_light(frame_bgr)` for verdadeiro (como
`vessel_ensemble_engine.run_ensemble` já fazia), aplicar `edge_score >= 0.35` como
filtro real, e chamar `is_plausible_vessel_size()` nos candidatos antes do NMS.

## 🟢 Nome não bate com o que roda — RESOLVIDO (WBF + BoT-SORT + DINOv2 + IMO OCR agora reais)

Wiring completo feito nesta rodada:

- **WBF**: já estava real dentro de `MultiDomainVesselDetector._fuse_by_iou` (achado ao
  reler o arquivo atual — tinha sido conectado por outra sessão em paralelo desde a
  última auditoria). Confirmado ao vivo via `fontes_detectoras` retornando múltiplas
  fontes reais por embarcação (`SixOpen_Y8Naval`, `MeWan2808_SAR_fluvial`, `COCO_generico`).
- **DINOv2 Re-ID**: conectado em `pluggable_pipeline.py`. Carrega `facebook/dinov2-small`
  de verdade (com checagem: se cair no fallback de CNN aleatória não-treinada, o recurso
  inteiro é desligado em vez de fingir Re-ID com ruído). Embedding real por candidato,
  usado na similaridade de aparência dentro do matching de `vessel_spatial_memory.py`
  (substitui a comparação grosseira por nome de cor quando disponível) e registrado numa
  **galeria persistente SQLite+HNSW** (`src/reid/sqlite_hnsw_gallery.py`) para Re-ID real
  entre reinicializações. Verificado ao vivo: `reid_embedding_ativo: true` em todas as
  embarcações, e um match real de galeria (`STS-BARCO-10` ~ `STS-BARCO-08`, similaridade
  cosseno 0.7836 — calculada de verdade, não fabricada).
- **BoT-SORT**: conectado em modo **não-calibrado** deliberadamente. O arquivo original
  (`bot_sort.py`) tinha o mesmo problema já visto em `vessel_spatial_memory.py`: uma
  `CameraGeometryConfig()` com pontos de controle fictícios do "Porto de Santos" que não
  correspondem à câmera real usada (qualquer link do YouTube configurado), então
  "velocidade em nós"/"dimensões em metros" derivadas dali seriam precisão fabricada.
  Corrigido: `camera_geometry=None` por padrão agora significa genuinely sem calibração
  (antes criava a config fictícia mesmo assim); velocidade honesta fica em px/s +
  rumo em graus reais (geometria pura, não precisa calibração), e `speed_knots`/
  `metric_dimensions` ficam `None` explicitamente em vez de usar uma constante arbitrária
  "0.5 m/px" que existia no fallback original. Usado no pipeline só para reforçar a
  confiança de uma detecção quando o Kalman+custo de aparência confirma continuidade
  real entre frames (`reforcado_por_botsort`), sem substituir a identidade/cinemática já
  validada do `VesselSpatialMemoryTracker`. **Nota**: esse tracker mais antigo (usado para
  nome/velocidade/destino exibidos hoje) ainda tem o problema original de fabricação de
  nós/destinos por nome fixo via a mesma `CameraGeometryConfig` fictícia — não foi tocado
  nesta rodada (fora do escopo pedido) e continua pendente de uma correção dedicada.
- **IMO OCR**: já rodava de verdade (EasyOCR + validação de dígito verificador IMO real em
  `vessel_fingerprinter.py`), mas tinha DOIS problemas: (1) o toggle `enable_ocr` nunca
  era lido — OCR sempre rodava, mesmo desligado na UI; (2) bug de nomenclatura que eu
  mesmo introduzi na rodada anterior — o fix do "IMO 9074729" fabricado passou a ler
  `fingerprint.texto_extraido.imo_number`, um campo que `generate_unique_fingerprint`
  nunca gerava (só existia `numero_imo`), então nenhuma leitura real de OCR chegava mais
  à tela, mesmo quando o OCR encontrava algo. Ambos corrigidos: toggle agora
  desliga a chamada ao EasyOCR de verdade (testado), e o campo `texto_extraido` passou a
  ser gerado corretamente.

Custo honesto a declarar: com Re-ID (DINOv2) + OCR (EasyOCR) rodando em CPU para cada
embarcação a cada frame, a latência por frame subiu para ~3s numa cena com 8 embarcações
(medido ao vivo). Isso é standard esperar. Se o vídeo ficar
perceptivelmente lento, desligar `enable_vit_reid`/`enable_ocr` na UI reduz o custo.

Ainda não conectados nesta rodada (não fazem parte do que o preset nomeia
explicitamente, e não foram pedidos): `tiled_inference.py`, `confidence_calibrator.py`
(esses dois já rodam dentro de `MultiDomainVesselDetector`, na verdade — só não
confirmei linha a linha se estão calibrados/efetivos), `state_anchor_manager.py`
(usado só dentro do `bot_sort.py` novo, não no tracker antigo), `tracklet_diversity_miner.py`,
`two_stage_text_engine.py` (a versão "duas etapas" com MSER; o OCR real que roda hoje é a
versão de um estágio em `vessel_fingerprinter.py`), `multiframe_consensus.py`, `src/filtering/*`,
`src/evaluation/*`. Nenhum destes é citado no nome do preset, então não bloqueiam a
alegação "WBF + BoT-SORT + DINOv2 + IMO OCR" — mas continuam mortos se algum dia o nome
do preset for expandido para citá-los.

## 🟡 Domínios "especialistas" sem pesos próprios

`urban_traffic_detector`, `indoor_occupancy_detector` etc. (em `domain_config.py`)
não têm arquivo de pesos dedicado — todos caem no mesmo `yolo11n.pt`/`yolov8n.pt`
genérico COCO (80 classes). Como COCO não tem classes como "faixa_pedestre",
"extintor", "camera_seguranca", "pegada_rastro", a maioria das taxonomias
customizadas de cada domínio (`domain_config.py`, campo `"classes"`) não pode ser
detectada por esses modelos. O único caminho realista pra essas classes
customizadas é o Gemini zero-shot (`gemini_annotator.py`), que exige API key do
usuário e não é usado automaticamente no loop de vídeo ao vivo.

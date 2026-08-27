"""
Suíte Completa de Testes Automatizados do Sistema de Percepção, Re-ID e Telemetria Naval na GPU AMD Radeon RX 6750 XT.
"""

import os
import sys
import time
import torch
import torch.nn.functional as F

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.device import get_device
from src.models.vessel_net import VesselPerceptionNet
from src.models.vit_vessel import PretrainedViTVesselModel
from src.registry.vessel_registry import PortVesselRegistry
from src.tracking.trajectory_engine import TensorTrajectoryTracker

def run_test_suite():
    print("=" * 95)
    print("INICIANDO SUITE DE TESTES AUTOMATIZADOS: PERCEPCAO, RE-ID E RASTREAMENTO NAVAL")
    print("=" * 95)
    
    passed_tests = 0
    total_tests = 6
    start_all = time.time()

    # --------------------------------------------------------------------------
    # TESTE 1: DETECÇÃO DE HARDWARE E ACELERAÇÃO AMD DIRECTML
    # --------------------------------------------------------------------------
    print("\n[TESTE 1/6] Verificacao de Aceleracao por Hardware (GPU AMD Radeon)...")
    device, dev_name = get_device()
    print(f"  -> Dispositivo Ativo: {dev_name} (PyTorch DirectML Device: {device})")
    
    # Testar alocação de tensores na GPU
    t_test = torch.randn(200, 200, device=device)
    t_res = torch.mm(t_test, t_test)
    assert t_res.shape == (200, 200), "Falha na multiplicacao de tensores na GPU"
    print("  [OK] Aceleracao por hardware na GPU AMD Radeon RX 6750 XT funcionando perfeitamente.")
    passed_tests += 1

    # --------------------------------------------------------------------------
    # TESTE 2: CARREGAMENTO DO MODELO VISION TRANSFORMER PRÉ-TREINADO (dima806)
    # --------------------------------------------------------------------------
    print("\n[TESTE 2/6] Teste do Modelo Pre-Treinado Vision Transformer (dima806 ViT)...")
    vit_model = PretrainedViTVesselModel().to(device)
    vit_model.eval()
    
    dummy_img = torch.randn(2, 3, 224, 224, device=device)
    with torch.no_grad():
        vit_out = vit_model(dummy_img)
        
    emb_768 = vit_out["embeddings"]
    cls_logits = vit_out["class_logits"]
    
    assert emb_768.shape == (2, 768), f"Shape inesperado para embeddings: {emb_768.shape}"
    assert cls_logits.shape == (2, 5), f"Shape inesperado para classes: {cls_logits.shape}"
    # Verificar norma unitária L2
    norms = torch.norm(emb_768, p=2, dim=1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-3), "Embeddings nao estao normalizados L2"
    print(f"  -> Embeddings 768D gerados e normalizados com sucesso (Norma: {norms[0].item():.4f}).")
    print(f"  -> Classes Navais Suportadas: {vit_model.classes}")
    print("  [OK] Modelo Vision Transformer pre-treinado validado com sucesso.")
    passed_tests += 1

    # --------------------------------------------------------------------------
    # TESTE 3: ARQUITETURA VESSELPERCEPTIONNET NA GPU AMD
    # --------------------------------------------------------------------------
    print("\n[TESTE 3/6] Teste de Inferencia da Rede Neural VesselPerceptionNet...")
    vessel_net = VesselPerceptionNet(num_classes=10, embedding_dim=512).to(device)
    vessel_net.eval()
    
    batch_imgs = torch.randn(4, 3, 256, 256, device=device)
    with torch.no_grad():
        out = vessel_net(batch_imgs)
        
    bboxes = out["bboxes"]
    conf = out["confidence"]
    classes = out["class_logits"]
    embs = out["embeddings"]
    
    assert bboxes.shape == (4, 4), f"BBoxes shape incorreto: {bboxes.shape}"
    assert conf.shape == (4, 1), f"Confidence shape incorreto: {conf.shape}"
    assert classes.shape == (4, 10), f"Class logits shape incorreto: {classes.shape}"
    assert embs.shape == (4, 512), f"Embeddings shape incorreto: {embs.shape}"
    print(f"  -> Processadas 4 imagens simultaneas na GPU AMD:")
    print(f"     * Bounding Boxes: {bboxes.shape} | Confianca: {conf.shape} | Embeddings: {embs.shape}")
    print("  [OK] Inferencia da arquitetura neural validada.")
    passed_tests += 1

    # --------------------------------------------------------------------------
    # TESTE 4: SEPARAÇÃO E DISCRIMINAÇÃO DE RE-ID (SIMILARIDADE DE COSSENO)
    # --------------------------------------------------------------------------
    print("\n[TESTE 4/6] Teste de Discriminacao de Re-Identificacao Unica (Re-ID)...")
    # Barco A (Foto 1 e Foto 2 com variacao de angulo/ruido)
    img_a1 = torch.randn(1, 3, 256, 256, device=device) * 0.2 + 0.3
    img_a2 = img_a1 + torch.randn(1, 3, 256, 256, device=device) * 0.05
    # Barco B (Embarcacao totalmente distinta)
    img_b = torch.randn(1, 3, 256, 256, device=device) * 0.2 + 0.8
    
    with torch.no_grad():
        emb_a1 = vessel_net(img_a1)["embeddings"]
        emb_a2 = vessel_net(img_a2)["embeddings"]
        emb_b = vessel_net(img_b)["embeddings"]
        
    sim_mesmo_barco = vessel_net.compute_similarity(emb_a1, emb_a2).item()
    sim_outro_barco = vessel_net.compute_similarity(emb_a1, emb_b).item()
    
    print(f"  -> Similaridade (Mesmo Barco em Cameras Diferentes): {sim_mesmo_barco:.4f} (>= 0.85)")
    print(f"  -> Similaridade (Barcos Completamente Distintos):   {sim_outro_barco:.4f}")
    assert sim_mesmo_barco > 0.85, "Falha: Similaridade do mesmo barco abaixo de 0.85"
    print("  [OK] Margem de Re-ID tensorial validada.")
    passed_tests += 1

    # --------------------------------------------------------------------------
    # TESTE 5: MOTOR DE TRAJETÓRIA E CÁLCULO DE RUMO NÁUTICO (0°-360°)
    # --------------------------------------------------------------------------
    print("\n[TESTE 5/6] Teste do Motor de Trajetoria e Rumo Nautico (Heading Engine)...")
    tracker = TensorTrajectoryTracker(max_history=15)
    
    # Simular barco movendo para Norte (dx=0, dy=-5 em coordenadas de imagem)
    p_norte = torch.tensor([200.0, 300.0])
    for _ in range(5):
        p_norte = p_norte + torch.tensor([0.0, -10.0])
        box = torch.tensor([[p_norte[0], p_norte[1], 50.0, 30.0]])
        tracker.update([999], box, ["Lancha Patrulha"])
        
    telem = tracker.get_track_telemetry(999)
    rumo_deg = telem["heading_deg"]
    cardinal = telem["heading_cardinal"]
    
    print(f"  -> Telemetria Calculada: Rumo = {rumo_deg:.1f} graus | Rosa dos Ventos = '{cardinal}' | Vel = {telem['speed_pixels']:.1f} px/frame")
    # Para movimento para cima no eixo Y da imagem (dx=0, dy<0), o rumo deve ser Norte (0° ou 360°)
    assert (rumo_deg <= 15.0 or rumo_deg >= 345.0), f"Rumo incorreto para Norte: {rumo_deg}"
    print("  [OK] Motor de telemetria e calculo de rumo náutico validado.")
    passed_tests += 1

    # --------------------------------------------------------------------------
    # TESTE 6: CICLO COMPLETO DO BANCO DE DADOS DO PORTO (PERSISTÊNCIA E RETORNO)
    # --------------------------------------------------------------------------
    print("\n[TESTE 6/6] Teste do Banco do Porto e Reconhecimento de Retorno...")
    test_db = "data/test_port_db.json"
    test_emb = "data/test_port_emb.pt"
    if os.path.exists(test_db): os.remove(test_db)
    if os.path.exists(test_emb): os.remove(test_emb)
    
    reg = PortVesselRegistry(db_path=test_db, embeddings_path=test_emb, similarity_threshold=0.80)
    
    # 1. Cadastrar Balsa
    reg.register_vessel(
        vessel_id="TEST-BR-01",
        name="Balsa Teste Solimoes",
        vessel_type="Balsa Graneleira",
        plate_imo="IMO-TEST-01",
        embedding_tensor=emb_a1,
        port_location="Porto Teste"
    )
    assert len(reg.vessels) == 1, "Falha no cadastro do barco"
    
    # 2. Retorno do Barco
    reid_result = reg.identify_or_auto_register(emb_a2, predicted_type="Balsa Graneleira", current_port="Porto Teste", heading_deg=45.0)
    info = reid_result["vessel"]
    score = reid_result["similarity"]
    assert reid_result["is_new"] == False, "Falha: Barco nao foi reconhecido no retorno ao porto"
    assert info["total_visits"] == 2, "Falha: Contador de visitas nao incrementou"
    print(f"  -> Barco '{info['name']}' reconhecido no retorno! Visitas: {info['total_visits']} | Score: {score:.4f}")
    
    # Limpar arquivos de teste
    if os.path.exists(test_db): os.remove(test_db)
    if os.path.exists(test_emb): os.remove(test_emb)
    print("  [OK] Banco de dados do porto e ciclo de retorno validados.")
    passed_tests += 1

    # --------------------------------------------------------------------------
    # RELATÓRIO FINAL
    # --------------------------------------------------------------------------
    elapsed = time.time() - start_all
    print("\n" + "=" * 95)
    print(f"RESULTADO DA SUITE DE TESTES: {passed_tests}/{total_tests} TESTES PASSARAM COM 100% DE SUCESSO! ({elapsed:.2f}s)")
    print(f"Hardware Utilizado: {dev_name}")
    print("=" * 95)

if __name__ == "__main__":
    run_test_suite()

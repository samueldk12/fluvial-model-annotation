"""
Script de Treinamento e Teste Prático do Sistema de Re-Identificação e Retorno de Embarcações ao Porto na GPU AMD Radeon.
"""

import os
import sys
import torch
import numpy as np

# Configurar saída UTF-8 para terminais Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.device import get_device
from src.models.vessel_net import VesselPerceptionNet
from src.registry.vessel_registry import PortVesselRegistry
from src.tracking.trajectory_engine import TensorTrajectoryTracker
from src.train import train_model

def run_port_lifecycle_test():
    device, dev_name = get_device()
    print("=" * 90)
    print(f"TESTE COMPLETO NA {dev_name.upper()}: CADASTRO, RE-ID E RETORNO AO PORTO")
    print("=" * 90)

    # 1. Treinar o modelo neural na GPU AMD
    print(f"\n[ETAPA 1] Treinando o modelo neural na {dev_name} com Triplet Loss para Re-ID...")
    ckpt_path = train_model(epochs=6, batch_size=16)

    # Carregar pesos (padrão DirectML: carrega para CPU e transfere para a GPU AMD)
    model = VesselPerceptionNet(num_classes=10, embedding_dim=512)
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device)
    model.eval()

    # 2. Inicializar o Banco de Dados do Porto
    db_file = "data/vessel_port_database.json"
    emb_file = "data/vessel_embeddings.pt"
    
    if os.path.exists(db_file):
        os.remove(db_file)
    if os.path.exists(emb_file):
        os.remove(emb_file)

    registry = PortVesselRegistry(db_path=db_file, embeddings_path=emb_file, similarity_threshold=0.82)

    # --------------------------------------------------------------------------
    # CENÁRIO 1: CADASTRO INICIAL DE 3 EMBARCAÇÕES NO PORTO (DIA 1)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print(f"CENARIO 1: CADASTRO DE EMBARCACOES NA PRIMEIRA CHEGADA AO PORTO (PROCESSADO NA {dev_name.upper()})")
    print("-" * 90)

    torch.manual_seed(42)
    img_balsa = (torch.randn(1, 3, 256, 256) * 0.1 + 0.2).to(device)
    img_petroleiro = (torch.randn(1, 3, 256, 256) * 0.1 + 0.6).to(device)
    img_patrulha = (torch.randn(1, 3, 256, 256) * 0.1 + 0.9).to(device)

    with torch.no_grad():
        emb_balsa = model(img_balsa)["embeddings"]
        emb_petroleiro = model(img_petroleiro)["embeddings"]
        emb_patrulha = model(img_patrulha)["embeddings"]

    registry.register_vessel(
        vessel_id="BR-SOL-101",
        name="Balsa Graneleira Rio Solimoes I",
        vessel_type="Balsa Graneleira",
        plate_imo="IMO-9482110",
        embedding_tensor=emb_balsa,
        port_location="Porto Fluvial de Manaus - Cais 01"
    )

    registry.register_vessel(
        vessel_id="BR-PET-900",
        name="Petroleiro Amazonia Master",
        vessel_type="Petroleiro Fluvial",
        plate_imo="IMO-8819204",
        embedding_tensor=emb_petroleiro,
        port_location="Terminal Aquaviario de Petroleo"
    )

    registry.register_vessel(
        vessel_id="BR-PAT-040",
        name="Lancha Patrulha Guardiana das Aguas",
        vessel_type="Embarcacao de Seguranca",
        plate_imo="MAR-PAT-04",
        embedding_tensor=emb_patrulha,
        port_location="Base Fluvial Integrada"
    )

    print(f"\n-> Total de embarcacoes persistidas no banco: {len(registry.vessels)}")

    # --------------------------------------------------------------------------
    # CENÁRIO 2: RETORNO DA BALSA AO PORTO DIAS DEPOIS (MUDANÇA DE LUZ E ÂNGULO)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("CENARIO 2: EMBARCACAO RETORNANDO AO PORTO DIAS DEPOIS (CAMERA 03 - OUTRO ANGULO)")
    print("-" * 90)

    img_balsa_retorno = img_balsa + (torch.randn(1, 3, 256, 256) * 0.05).to(device)

    with torch.no_grad():
        emb_retorno = model(img_balsa_retorno)["embeddings"]

    heading_aproximacao = 65.4

    is_recognized, vessel_info, score = registry.identify_vessel(
        query_embedding=emb_retorno,
        current_port="Porto Fluvial de Manaus - Cais 03",
        heading_deg=heading_aproximacao
    )

    if is_recognized:
        print(f"[RE-ID SUCESSO] EMBARCACAO IDENTIFICADA COM SUCESSO NO RETORNO AO PORTO!")
        print(f"   * Hardware de Inferencia: {dev_name}")
        print(f"   * Nome Cadastrado:        {vessel_info['name']}")
        print(f"   * ID / Matricula:         {vessel_info['vessel_id']} (Registro: {vessel_info['plate_imo']})")
        print(f"   * Tipo:                   {vessel_info['type']}")
        print(f"   * Similaridade Re-ID:     {score:.4f} (Score de Confianca: {score*100:.1f}%)")
        print(f"   * Total de Visitas:       {vessel_info['total_visits']} registro(s)")
        print(f"   * Primeiro Cadastro:      {vessel_info['first_registered']}")
        print(f"   * Ultima Entrada:         {vessel_info['last_seen']}")
        print(f"   * Rumo de Entrada:        {heading_aproximacao:.1f} graus (Leste-Nordeste)")
    else:
        print(f"[ALERTA] Embarcacao nao reconhecida (Similaridade: {score:.4f})")

    # --------------------------------------------------------------------------
    # CENÁRIO 3: CHEGADA DE UMA EMBARCAÇÃO TOTALMENTE NOVA / DESCONHECIDA
    # --------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("CENARIO 3: CHEGADA DE UMA NOVA EMBARCACAO ESTRANHA (NAO CADASTRADA)")
    print("-" * 90)

    img_desconhecido = (torch.randn(1, 3, 256, 256) * 0.4 - 0.5).to(device)
    with torch.no_grad():
        emb_desconhecido = model(img_desconhecido)["embeddings"]

    is_recognized, vessel_info, score = registry.identify_vessel(
        query_embedding=emb_desconhecido,
        current_port="Porto de Itacoatiara",
        heading_deg=180.0
    )

    if is_recognized:
        print(f"[RE-ID] Embarcacao reconhecida como: {vessel_info['name']} (Score: {score:.4f})")
    else:
        print(f"[NOVA EMBARCACAO DETECTADA] - Nao consta no banco cadastral do porto.")
        print(f"   * Maior Similaridade no Banco: {score:.4f} (Abaixo do limiar de {registry.similarity_threshold})")
        print(f"   -> Realizando auto-cadastro no sistema...")
        registry.register_vessel(
            vessel_id="BR-CAT-550",
            name="Catamara Regional Expresso do Rio",
            vessel_type="Transporte de Passageiros",
            plate_imo="PAS-2026-X",
            embedding_tensor=emb_desconhecido,
            port_location="Porto de Itacoatiara"
        )

    print("\n" + "=" * 90)
    print(f"TESTE FINALIZADO NA {dev_name.upper()}: O banco agora possui {len(registry.vessels)} embarcacoes salvas.")
    print(f"Arquivos persistidos em disco: '{db_file}' e '{emb_file}'")
    print("=" * 90)

if __name__ == "__main__":
    run_port_lifecycle_test()

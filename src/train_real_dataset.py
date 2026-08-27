"""
Script de Treinamento Rápido com o Dataset Real Completo na GPU AMD Radeon RX 6750 XT.
"""

import os
import sys
import time
import torch
from torch.utils.data import DataLoader

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.device import get_device
from src.models.vessel_net import VesselPerceptionNet
from src.data.real_vessel_dataset import InMemoryRealVesselDataset
from src.losses.multitask_loss import MultiTaskVesselLoss

def train_real_model(epochs=6, batch_size=32, lr=1e-3, save_path="checkpoints/vessel_perception_net_real.pt"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    device, dev_name = get_device()
    print("=" * 90)
    print(f"TREINAMENTO COM DATASET REAL NA {dev_name.upper()}")
    print("=" * 90)

    # 1. Carregar Dataset Real em RAM
    dataset = InMemoryRealVesselDataset(img_size=(128, 128))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    # 2. Inicializar Modelo e Otimizador
    model = VesselPerceptionNet(num_classes=10, embedding_dim=512).to(device)
    criterion = MultiTaskVesselLoss(w_bbox=1.0, w_cls=1.0, w_triplet=2.0, triplet_margin=0.5)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    print(f"\n-> Iniciando treinamento por {epochs} épocas na GPU AMD...")
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        start_time = time.time()

        for batch in loader:
            optimizer.zero_grad()

            images = batch["image"].to(device)
            targets = {
                "bbox": batch["bbox"].to(device),
                "class_label": batch["class_label"].to(device)
            }
            outputs = model(images)
            loss_det, _ = criterion(outputs, targets)

            # Triplet Re-ID
            positives = batch["positive"].to(device)
            negatives = batch["negative"].to(device)

            emb_anchor = outputs["embeddings"]
            emb_pos = model(positives)["embeddings"]
            emb_neg = model(negatives)["embeddings"]

            loss_triplet = criterion.compute_triplet_loss(emb_anchor, emb_pos, emb_neg)

            batch_loss = loss_det + loss_triplet
            batch_loss.backward()
            optimizer.step()

            total_loss += batch_loss.item()

        scheduler.step()
        elapsed = time.time() - start_time
        avg_loss = total_loss / len(loader)

        print(f"Epoca [{epoch:02d}/{epochs:02d}] | Perda Media: {avg_loss:.4f} | "
              f"Det: {loss_det.item():.4f} | Triplet: {loss_triplet.item():.4f} | Tempo: {elapsed:.2f}s")

    # Salvar Checkpoint Real
    torch.save({
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "loss": avg_loss,
        "device": str(device),
        "num_samples": len(dataset)
    }, save_path)

    print("\n" + "=" * 90)
    print(f"[SUCESSO] Treinamento com 2.660 imagens reais concluido na {dev_name}!")
    print(f"Modelo salvo em: '{save_path}'")
    print("=" * 90)
    return save_path

if __name__ == "__main__":
    train_real_model(epochs=6, batch_size=32)

"""
Pipeline de Treinamento em PyTorch da VesselPerceptionNet com Suporte à GPU AMD Radeon.
"""

import os
import sys
import time
import torch
from torch.utils.data import DataLoader

# Configurar saída UTF-8 para terminais Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.device import get_device
from src.models.vessel_net import VesselPerceptionNet
from src.data.vessel_dataset import SyntheticVesselDataset, TripletVesselDataset
from src.losses.multitask_loss import MultiTaskVesselLoss

def train_model(epochs=6, batch_size=16, lr=2e-3, save_dir="checkpoints"):
    os.makedirs(save_dir, exist_ok=True)
    device, dev_name = get_device()
    print("=" * 85)
    print(f"INICIANDO TREINAMENTO DA VESSELPERCEPTIONNET NO DISPOSITIVO: {dev_name}")
    print("=" * 85)

    # 1. Instanciar Modelo e Datasets
    model = VesselPerceptionNet(num_classes=10, embedding_dim=512).to(device)
    
    det_dataset = SyntheticVesselDataset(num_samples=320, img_size=(128, 128))
    triplet_dataset = TripletVesselDataset(num_triplets=320, img_size=(128, 128))
    
    det_loader = DataLoader(det_dataset, batch_size=batch_size, shuffle=True)
    triplet_loader = DataLoader(triplet_dataset, batch_size=batch_size, shuffle=True)

    # 2. Otimizador e Perda com Margem de Re-ID Robusta
    criterion = MultiTaskVesselLoss(w_bbox=1.0, w_cls=1.0, w_triplet=2.0, triplet_margin=0.5)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # 3. Loop de Épocas
    for epoch in range(1, epochs + 1):
        model.train()
        total_epoch_loss = 0.0
        start_time = time.time()

        for (det_batch, trip_batch) in zip(det_loader, triplet_loader):
            optimizer.zero_grad()

            # Fase 1: Detecção e Classificação
            images = det_batch["image"].to(device)
            targets = {
                "bbox": det_batch["bbox"].to(device),
                "class_label": det_batch["class_label"].to(device)
            }
            outputs = model(images)
            loss_det, loss_dict = criterion(outputs, targets)

            # Fase 2: Re-Identificação por Triplas (Âncora, Positivo, Negativo)
            anchors = trip_batch["anchor"].to(device)
            positives = trip_batch["positive"].to(device)
            negatives = trip_batch["negative"].to(device)

            emb_anchor = model(anchors)["embeddings"]
            emb_pos = model(positives)["embeddings"]
            emb_neg = model(negatives)["embeddings"]

            loss_triplet = criterion.compute_triplet_loss(emb_anchor, emb_pos, emb_neg)

            # Perda Multitarefa Total
            total_loss = loss_det + loss_triplet
            total_loss.backward()
            optimizer.step()

            total_epoch_loss += total_loss.item()

        scheduler.step()
        elapsed = time.time() - start_time
        avg_loss = total_epoch_loss / len(det_loader)

        print(f"Epoca [{epoch:02d}/{epochs:02d}] | Perda: {avg_loss:.4f} | "
              f"Det: {loss_det.item():.4f} | Triplet: {loss_triplet.item():.4f} | Tempo: {elapsed:.2f}s")

    # 4. Salvar Checkpoint Treinado
    checkpoint_path = os.path.join(save_dir, "vessel_perception_net.pt")
    torch.save({
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": avg_loss,
        "device_used": str(device)
    }, checkpoint_path)
    
    print("\n" + "=" * 85)
    print(f"[SUCESSO] Treinamento na GPU AMD concluido! Modelo salvo em: {checkpoint_path}")
    print("=" * 85)
    return checkpoint_path

if __name__ == "__main__":
    train_model(epochs=6, batch_size=16)

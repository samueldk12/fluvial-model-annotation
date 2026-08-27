"""
Módulo de Re-Identificação Única de Embarcações (Vessel Re-ID e Fingerprinting Visual).

Demonstra como:
1. Extrair embeddings visuais (vetores de características de 768 dimensoes) de fotos de barcos usando Vision Transformers (ViT).
2. Comparar dois barcos usando Similaridade de Cosseno para determinar se e o MESMO barco (Re-Identificacao).
3. Indexar embarcacoes em uma galeria para busca e recuperacao automatica em diferentes cameras portuarias/fluviais.
"""

import math
import numpy as np

class VesselReIDMatcher:
    def __init__(self, similarity_threshold=0.82):
        self.similarity_threshold = similarity_threshold
        self.gallery = {} # vessel_unique_id -> {'embedding': np.array, 'meta': dict}

    def register_vessel(self, unique_id, embedding, metadata=None):
        """
        Cadastra uma embarcacao na galeria com sua assinatura visual unica.
        """
        # Normalizar embedding para norma unitaria
        norm_emb = embedding / (np.linalg.norm(embedding) + 1e-8)
        self.gallery[unique_id] = {
            "embedding": norm_emb,
            "meta": metadata or {}
        }

    def query_vessel(self, query_embedding):
        """
        Compara o embedding do barco detectado contra a galeria cadastrada.
        Retorna (matched_unique_id, similarity_score)
        """
        norm_query = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        
        best_id = None
        best_score = -1.0
        
        for unique_id, data in self.gallery.items():
            # Similaridade de Cosseno: dot product de vetores normalizados
            score = float(np.dot(norm_query, data["embedding"]))
            if score > best_score:
                best_score = score
                best_id = unique_id
                
        is_match = (best_score >= self.similarity_threshold)
        return best_id, best_score, is_match

def simulate_vessel_reid_demo():
    print("=" * 80)
    print("DEMONSTRACAO DE RE-IDENTIFICACAO UNICA DE EMBARCACOES (VESSEL RE-ID)")
    print("=" * 80)
    
    matcher = VesselReIDMatcher(similarity_threshold=0.80)
    
    # 1. Simular cadastro de 3 barcos na Camera 1 (Porto/Fluvial Ponto A)
    np.random.seed(42)
    # Embedding base caracteristico para 3 barcos distintos
    emb_barco_alpha = np.random.randn(768)
    emb_barco_beta = np.random.randn(768)
    emb_barco_gamma = np.random.randn(768)
    
    matcher.register_vessel("BARCO_PETROLEIRO_01", emb_barco_alpha, {"tipo": "Tanker", "porte": "Grande"})
    matcher.register_vessel("BALSA_GRANELEIRA_07", emb_barco_beta, {"tipo": "Barge", "porte": "Medio"})
    matcher.register_vessel("LANCHA_PESQUEIRA_44", emb_barco_gamma, {"tipo": "Fishing", "porte": "Pequeno"})
    
    print("[1] Embarcacoes cadastradas na Galeria da Camera 1 (Ponto A):")
    for vid in matcher.gallery:
        print(f"    - ID: {vid} | Tipo: {matcher.gallery[vid]['meta']['tipo']}")
        
    print("\n[2] Nova deteccao na Camera 2 (Ponto B - 5 km rio abaixo com mudanca de angulo e luz):")
    # Simula o mesmo barco Alpha visto na Camera 2 com leve ruido visual (variacao de iluminacao/angulo)
    query_same_alpha = emb_barco_alpha + np.random.randn(768) * 0.15
    matched_id, score, is_match = matcher.query_vessel(query_same_alpha)
    print(f"    -> Consulta Barco Novo vs Galeria: Match={matched_id} | Score Cosseno={score:.4f} | Reconhecido? {'SIM' if is_match else 'NAO'}")
    
    print("\n[3] Nova deteccao de um Barco Desconhecido (Nao cadastrado):")
    emb_desconhecido = np.random.randn(768)
    matched_id, score, is_match = matcher.query_vessel(emb_desconhecido)
    print(f"    -> Consulta Barco Novo vs Galeria: Melhor Candidato={matched_id} | Score Cosseno={score:.4f} | Reconhecido? {'SIM' if is_match else 'NOVO BARCO REGISTRADO'}")
    print("=" * 80)

if __name__ == "__main__":
    simulate_vessel_reid_demo()

import numpy as np

class ReIDEvaluator:
    def __init__(self):
        pass

    def evaluate(self, query_embeddings, query_ids, gallery_embeddings, gallery_ids):
        q_embs = np.array(query_embeddings, dtype=np.float32)
        g_embs = np.array(gallery_embeddings, dtype=np.float32)

        q_norms = np.linalg.norm(q_embs, axis=1, keepdims=True)
        g_norms = np.linalg.norm(g_embs, axis=1, keepdims=True)
        q_embs = q_embs / np.maximum(1e-7, q_norms)
        g_embs = g_embs / np.maximum(1e-7, g_norms)

        sim_matrix = q_embs @ g_embs.T

        num_queries = len(query_ids)
        rank1_hits = 0
        rank5_hits = 0
        all_ap = []

        all_genuine_scores = []
        all_impostor_scores = []

        for i in range(num_queries):
            target_id = query_ids[i]
            scores = sim_matrix[i]
            sorted_indices = np.argsort(scores)[::-1]

            ranked_gallery_ids = [gallery_ids[idx] for idx in sorted_indices]
            matches = (np.array(ranked_gallery_ids) == target_id)

            if len(ranked_gallery_ids) > 0 and ranked_gallery_ids[0] == target_id:
                rank1_hits += 1
            if any(rg == target_id for rg in ranked_gallery_ids[:5]):
                rank5_hits += 1

            num_pos = np.sum(matches)
            if num_pos > 0:
                cum_matches = np.cumsum(matches)
                ranks = np.arange(1, len(matches) + 1)
                precision_at_k = cum_matches / ranks
                ap = np.sum(precision_at_k * matches) / num_pos
                all_ap.append(ap)
            else:
                all_ap.append(0.0)

            for j, g_id in enumerate(gallery_ids):
                if g_id == target_id:
                    all_genuine_scores.append(scores[j])
                else:
                    all_impostor_scores.append(scores[j])

        rank1 = float(rank1_hits / max(1, num_queries))
        rank5 = float(rank5_hits / max(1, num_queries))
        mean_ap = float(np.mean(all_ap)) if all_ap else 0.0

        tar_at_far_1pct = 0.0
        if all_impostor_scores and all_genuine_scores:
            impostors = np.sort(all_impostor_scores)[::-1]
            far_index = max(0, int(round(len(impostors) * 0.01)) - 1)
            thresh_at_1pct_far = impostors[far_index]

            gen_accepted = np.sum(np.array(all_genuine_scores) >= thresh_at_1pct_far)
            tar_at_far_1pct = float(gen_accepted / max(1, len(all_genuine_scores)))

        return {
            'cmc_rank1': rank1,
            'cmc_rank5': rank5,
            'map': mean_ap,
            'tar_at_far_1pct': tar_at_far_1pct,
            'num_queries': num_queries,
            'gallery_size': len(gallery_ids)
        }

import os
import json
import sqlite3
import numpy as np

try:
    import hnswlib
    _HAS_HNSW = True
except ImportError:
    _HAS_HNSW = False

class VesselReIDGallery:
    def __init__(self, db_path='data/vessel_gallery.db', embedding_dim=384, max_elements=5000):
        self.db_path = db_path
        self.embedding_dim = int(embedding_dim)
        self.max_elements = int(max_elements)
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        self._init_db()

        self.index = None
        self.id_to_vessel_id = {}
        self.vessel_id_to_id = {}
        self.next_int_id = 0

        if _HAS_HNSW:
            self.index = hnswlib.Index(space='cosine', dim=self.embedding_dim)
            self.index.init_index(max_elements=self.max_elements, ef_construction=200, M=16)
            self.index.set_ef(50)

        self._load_existing_from_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vessels (
                    vessel_id TEXT PRIMARY KEY,
                    name TEXT,
                    imo TEXT,
                    category_5classes TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    num_tracklets INTEGER,
                    embedding_blob BLOB,
                    metadata_json TEXT
                )
            ''')
            conn.commit()

    def _load_existing_from_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT vessel_id, embedding_blob FROM vessels')
            rows = cursor.fetchall()
            for v_id, blob in rows:
                if blob is not None:
                    emb = np.frombuffer(blob, dtype=np.float32)
                    if len(emb) == self.embedding_dim:
                        int_id = self.next_int_id
                        self.next_int_id += 1
                        self.id_to_vessel_id[int_id] = v_id
                        self.vessel_id_to_id[v_id] = int_id
                        if self.index is not None:
                            self.index.add_items(emb.reshape(1, -1), np.array([int_id]))

    def register_or_update_vessel(self, vessel_id, embedding, metadata=None):
        if embedding is None:
            return False

        emb_arr = np.array(embedding, dtype=np.float32).flatten()
        norm = np.linalg.norm(emb_arr)
        if norm > 1e-7:
            emb_arr = emb_arr / norm

        meta = metadata or {}
        name = meta.get('name', f'Embarcacao {vessel_id}')
        imo = meta.get('imo', '')
        category = meta.get('category_5classes', 'Embarcacao')
        first_seen = meta.get('first_seen', '')
        last_seen = meta.get('last_seen', '')
        num_trk = int(meta.get('num_tracklets', 1))
        meta_json = json.dumps(meta, ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO vessels (vessel_id, name, imo, category_5classes, first_seen, last_seen, num_tracklets, embedding_blob, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vessel_id) DO UPDATE SET
                    name=excluded.name,
                    imo=excluded.imo,
                    category_5classes=excluded.category_5classes,
                    last_seen=excluded.last_seen,
                    num_tracklets=vessels.num_tracklets + 1,
                    embedding_blob=excluded.embedding_blob,
                    metadata_json=excluded.metadata_json
            ''', (vessel_id, name, imo, category, first_seen, last_seen, num_trk, emb_arr.tobytes(), meta_json))
            conn.commit()

        if vessel_id in self.vessel_id_to_id:
            int_id = self.vessel_id_to_id[vessel_id]
        else:
            int_id = self.next_int_id
            self.next_int_id += 1
            self.id_to_vessel_id[int_id] = vessel_id
            self.vessel_id_to_id[vessel_id] = int_id

        if self.index is not None:
            self.index.add_items(emb_arr.reshape(1, -1), np.array([int_id]))

        return True

    def search(self, query_embedding, k=5, similarity_threshold=0.60):
        if query_embedding is None or len(self.id_to_vessel_id) == 0:
            return []

        q_arr = np.array(query_embedding, dtype=np.float32).flatten()
        norm = np.linalg.norm(q_arr)
        if norm > 1e-7:
            q_arr = q_arr / norm

        results = []
        if self.index is not None and self.index.get_current_count() > 0:
            eff_k = min(k, self.index.get_current_count())
            labels, distances = self.index.knn_query(q_arr.reshape(1, -1), k=eff_k)
            for int_id, dist in zip(labels[0], distances[0]):
                cos_sim = 1.0 - float(dist)
                if cos_sim >= similarity_threshold:
                    v_id = self.id_to_vessel_id.get(int_id)
                    if v_id:
                        v_info = self.get_vessel(v_id)
                        if v_info:
                            v_info['similarity_score'] = round(cos_sim, 4)
                            results.append(v_info)
        else:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT vessel_id, name, imo, category_5classes, first_seen, last_seen, num_tracklets, embedding_blob, metadata_json FROM vessels')
                for row in cursor.fetchall():
                    v_id, name, imo, cat, f_seen, l_seen, num_trk, blob, m_json = row
                    if blob:
                        emb = np.frombuffer(blob, dtype=np.float32)
                        cos_sim = float(np.dot(q_arr, emb))
                        if cos_sim >= similarity_threshold:
                            results.append({
                                'vessel_id': v_id,
                                'name': name,
                                'imo': imo,
                                'category_5classes': cat,
                                'first_seen': f_seen,
                                'last_seen': l_seen,
                                'num_tracklets': num_trk,
                                'metadata': json.loads(m_json) if m_json else {},
                                'similarity_score': round(cos_sim, 4)
                            })
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = results[:k]

        return results

    def get_vessel(self, vessel_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT vessel_id, name, imo, category_5classes, first_seen, last_seen, num_tracklets, metadata_json FROM vessels WHERE vessel_id = ?', (vessel_id,))
            row = cursor.fetchone()
            if row:
                v_id, name, imo, cat, f_seen, l_seen, num_trk, m_json = row
                return {
                    'vessel_id': v_id,
                    'name': name,
                    'imo': imo,
                    'category_5classes': cat,
                    'first_seen': f_seen,
                    'last_seen': l_seen,
                    'num_tracklets': num_trk,
                    'metadata': json.loads(m_json) if m_json else {}
                }
        return None

    def list_all_vessels(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT vessel_id, name, imo, category_5classes, first_seen, last_seen, num_tracklets FROM vessels ORDER BY last_seen DESC')
            return [{
                'vessel_id': r[0],
                'name': r[1],
                'imo': r[2],
                'category_5classes': r[3],
                'first_seen': r[4],
                'last_seen': r[5],
                'num_tracklets': r[6]
            } for r in cursor.fetchall()]

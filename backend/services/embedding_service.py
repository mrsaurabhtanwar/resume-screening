import os
import sys

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import json
import boto3
import faiss

import numpy as np

from typing import List, Tuple, Optional, Union
from sentence_transformers import SentenceTransformer
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from services.embedding_text import build_json_to_text, build_jobdes_json_to_text
from schema.resume import ResumeData
from schema.job_description import JobDescriptionData

load_dotenv()

_MODEL = None

def get_embedding_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        token = os.getenv("HF_TOKEN")
        _MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", token=token)
    return _MODEL

class FAISSS3VectorStore:
    def __init__(
        self,
        dimension: int = 384,
        bucket_name: Optional[str] = None,
        local_dir: str = "storage"
        ):
        self.dimension = dimension
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        self.local_dir = os.path.abspath(local_dir)
        os.makedirs(self.local_dir, exist_ok=True)

        self.local_index_path = os.path.join(self.local_dir, "faiss_index.bin")
        self.local_map_path = os.path.join(self.local_dir, "id_map.json")

        self.s3_index_key = "index/faiss_index.bin"
        self.s3_map_key = "index/id_map.json"

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )

        self.index = faiss.IndexFlatIP(self.dimension)
        self.candidate_map: List[str] = []

        self.load_index_from_s3()

    def load_index_from_s3(self) -> bool:
        try:
            self.s3_client.download_file(self.bucket_name, self.s3_index_key, self.local_index_path)
            self.s3_client.download_file(self.bucket_name, self.s3_map_key, self.local_map_path)

            self.index = faiss.read_index(self.local_index_path)
            with open(self.local_map_path, 'r', encoding="utf-8") as f:
                self.candidate_map = json.load(f)

            print(f"Loaded FAISS index from S3 ({self.index.ntotal} vectors)")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print("No existing FAISS index found on S3. Initializing fresh index.")
            else:
                print(f"S3 download warning: {e}")
        except Exception as e:
            print(f"S3 index load notice: {e}")

        return False

    def save_index_to_s3(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.local_index_path), exist_ok=True)
            faiss.write_index(self.index, self.local_index_path)
            with open(self.local_map_path, 'w', encoding="utf-8") as f:
                json.dump(self.candidate_map, f, indent=2)

            self.s3_client.upload_file(self.local_index_path, self.bucket_name, self.s3_index_key)
            self.s3_client.upload_file(self.local_map_path, self.bucket_name, self.s3_map_key)

            print(f"Synced FAISS index ({self.index.ntotal} vectors) to S3")
            return True
        except Exception as e:
            print(f"S3 index upload error: {e}")
            return False

    def add_candidate(self, candidate_id: str, resume_obj: ResumeData, sync_s3: bool = True) -> np.ndarray:
        embed_text = build_json_to_text(resume_obj)["full_text"]
        model = get_embedding_model()

        vector = model.encode([embed_text], convert_to_numpy=True).astype(np.float32)
        faiss.normalize_L2(vector)

        self.index.add(vector)
        self.candidate_map.append(candidate_id)

        if sync_s3:
            self.save_index_to_s3()

        return vector

    def search(self, jd_text: Union[JobDescriptionData, str], top_k: int = 5) -> List[Tuple[str, float]]:
        if self.index.ntotal == 0:
            return []

        if isinstance(jd_text, JobDescriptionData):
            embed_text = build_jobdes_json_to_text(jd_text)
        else:
            embed_text = str(jd_text)

        model = get_embedding_model()
        jd_vector = model.encode([embed_text], convert_to_numpy=True).astype(np.float32)
        faiss.normalize_L2(jd_vector)

        k = min(top_k, self.index.ntotal)
        similarities, indices = self.index.search(jd_vector, k)

        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if 0 <= idx < len(self.candidate_map):
                results.append((self.candidate_map[idx], float(sim)))

        return results

    def remove_candidate(self, candidate_id: str) -> bool:
        if candidate_id not in self.candidate_map:
            return False

        idx = self.candidate_map.index(candidate_id)
        self.candidate_map.pop(idx)

        new_index = faiss.IndexFlatIP(self.dimension)
        if self.index.ntotal > 1:
            all_vectors = np.array([self.index.reconstruct(i) for i in range(self.index.ntotal) if i != idx])
            new_index.add(all_vectors)

        self.index = new_index
        self.save_index_to_s3()
        return True

vector_store = FAISSS3VectorStore()

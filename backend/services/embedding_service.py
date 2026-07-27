import os
import json
import boto3
import faiss

import numpy as np

from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from services.embedding_text import build_json_to_text
from schema.resume import ResumeData
from schema.job_description import JobDescriptionData

load_dotenv()

token = os.getenv("HF_TOKEN")


class FAISSS3VectorStore:
    def __init__(
        self,
        dimension: int = 384,
        bucket_name: Optional[str] = None,
        local_dir: str = "storage"
        ):
        self.dimension = dimension
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        self.local_dir = local_dir
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
            print(f"[S3] Checking S3 for exiting index in bucket '{self.bucket_name}'...")
            self.s3_client.download_file(self.bucket_name, self.s3_index_key, self.local_index_path)
            self.s3_client.download_file(self.bucket_name, self.s3_map_key, self.local_map_path)

            self.index = faiss.read_index(self.local_index_path)
            with open(self.local_map_path, 'r', encoding="utf-8") as f:
                self.candidate_map = json.load(f)
                
            print(f"[S3] Successfully loaded FAISS index from S3! Total vectors: {self.index.ntotal}")
            return True
        
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print("[S#] No existing index found on S3. Initializing fresh index.")
            else:
                print(f"[S3 Waring] Error downloading from S3: {e}")
        except Exception as e:
            print(f"[S3 Waring] Could not load S3 index: {e}")
            
        return False
  
  
    def save_index_to_s3(self) -> bool:
        try:
            faiss.write_index(self.index, self.local_index_path)
            with open(self.local_map_path, 'w', encoding="utf-8") as f:
                json.dump(self.candidate_map, f, indent=2)
                
            self.s3_client.upload_file(self.local_index_path, self.bucket_name, self.s3_index_key)
            self.s3_client.upload_file(self.local_map_path, self.bucket_name, self.s3_map_key)
            
            print(f"[S3 Upload] Successfully synced FAISS index ({self.index.ntotal} vectors) to S3 under 'index/'!")
            return True
        except Exception as e:
            print(f"[S3 Error] failed to save/upload index to S3: {e}")
            return False
                  

    def add_candidate(self, candidate_id: str, resume_obj: ResumeData, sync_s3: bool = True) -> np.ndarray:
        embed_text = build_json_to_text(resume_obj)
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", token=token)
        
        vector = model.encode([embed_text], convert_to_numpy=True).astype(np.float32)
        faiss.normalize_L2(vector)
        
        self.index.add(vector)
        self.candidate_map.append(candidate_id)
        
        print(f"-> Added Candidate '{candidate_id}' to FAISS (Total: {self.index.ntotal})")
        
        if sync_s3:
            self.save_index_to_s3()
            
        return vector
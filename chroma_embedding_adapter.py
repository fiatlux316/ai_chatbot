"""
Chroma DB에 E5 임베딩 모델을 적용하기 위한 커스텀 어댑터
"""
import numpy as np
from es_embedding import E5QEmbeddings


class E5ChromaEmbeddings:
    """Chroma가 사용할 수 있는 E5 임베딩 래퍼"""
    
    def __init__(self):
        self.embedder = E5QEmbeddings()
    
    def name(self) -> str:
        """ChromaDB가 요구하는 embedding_function의 name 메소드"""
        return "E5ChromaEmbeddings"
    
    def __call__(self, input):
        """
        input: str 또는 List[str]
        output: List[List[float]] 형태의 임베딩 벡터
        """
        if isinstance(input, str):
            # 단일 텍스트
            embedding = self.embedder.embed_query(input)
            return [embedding.tolist()]
        elif isinstance(input, list):
            # 리스트 형태
            embeddings = []
            for text in input:
                embedding = self.embedder.embed_query(text)
                embeddings.append(embedding.tolist())
            return embeddings
        else:
            raise ValueError(f"Unsupported input type: {type(input)}")

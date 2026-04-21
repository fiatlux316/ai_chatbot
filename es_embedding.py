import requests
import json

import torch
import torch.nn.functional as F
import numpy as np
from transformers import AutoModel, AutoTokenizer
from torch import Tensor

import onnxruntime as ort
import onnx
import pathlib
import os
#from common.config import config

class E5QEmbeddings:
    def __init__(self, **kwargs):
        super().__init__()

        local_dir_nm = "multilingual-e5-large-quantized"

        if os.path.exists(local_dir_nm) is False:
            Exception("모델파일에러")

        self.model_path = pathlib.Path(local_dir_nm, 'multilingual-e5-large.opt.qint8.onnx')
        self.tokenizer_path = pathlib.Path(local_dir_nm)
        self.encoder = onnx.load(self.model_path, load_external_data=False)
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path)
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        provider = 'CPUExecutionProvider'
        assert provider in ort.get_all_providers(), f"provider {provider} not found"
        self.session = ort.InferenceSession(self.model_path, sess_options, providers=[provider])
        self.session.disable_fallback()

    def __pool__(self, last_hidden_states: Tensor,
                 attention_mask: Tensor,
                 pool_type: str) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)

        if pool_type == "avg":
            emb = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
        elif pool_type == "cls":
            emb = last_hidden[:, 0]
        else:
            raise ValueError(f"pool_type {pool_type} not supported")
        return emb

    @torch.no_grad()
    def embed_query(self, text: str) -> np.array:
        inputs = self.tokenizer([text], max_length=512,
                                padding=True,
                                truncation=True,
                                )
        ort_inputs = {'input_ids': inputs['input_ids'], 'attention_mask': inputs['attention_mask']}
        outputs = self.session.run(None, ort_inputs)[0]
        embeds = self.__pool__(torch.tensor(outputs[0]), torch.tensor(inputs['attention_mask']), 'avg')
        embeds = F.normalize(embeds, p=2, dim=-1).numpy()

        return embeds[0]


e5q_emb_model = E5QEmbeddings()


class Base_Request():
    def get_request(self, url):
        try:
            res = requests.get(url)
            return json.loads(res.text)
        except Exception as e:
            print(e)
        return str(e)

    def post_request(self, url, data):
        try:
            res = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json; charset=utf-8'})
            return json.loads(res.text)
        except Exception as e:
            print(e)
        return str(e)

    def put_request(self, url, data):
        try:
            res = requests.put(url, data=json.dumps(data), headers={'Content-Type': 'application/json; charset=utf-8'})
            return json.loads(res.text)
        except Exception as e:
            print(e)
        return str(e)

    def del_request(self, url):
        try:
            res = requests.delete(url)
            return [True, ""]
        except Exception as e:
            print(e)
        return [False, str(e)]


open_search_url = {
    "local": "",
    "dev": "vpc-dev-apne2-erody-search-vmaetfnjqtuhscfl3spvc6zhmm.ap-northeast-2.es.amazonaws.com",
    "stg": "vpc-dev-apne2-erody-search-vmaetfnjqtuhscfl3spvc6zhmm.ap-northeast-2.es.amazonaws.com", # 비용문제로 stg opensearch 삭제
    "prd": "vpc-prd-apne2-erody-search-iny3phj6yhlz6kfgqsiyrtn7cq.ap-northeast-2.es.amazonaws.com"
}

class Opensearch_Request(Base_Request):
    def __init__(self):
        env = 'dev' #config.ENV
        self.open_search_id = "admin"
        self.open_search_pw = "Admin12%23"  # 특수문자 인코딩
        self.open_search_url = open_search_url[env]

    def get_opensearch_info(self):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}"
        return self.get_request(URL)

    def get_index_info(self, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}"
        return self.get_request(URL)

    def delete_index(self, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}"
        return self.del_request(URL)

    def create_index(self, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}"

        data = {
            "settings": {
                "index.knn": "true"
            },
            "mappings": {
                "properties": {
                    "text_embedding": {
                        "type": "knn_vector",
                        "dimension": 1024
                    },
                    "text": {
                        "type": "text"
                    },
                    "id": {
                        "type": "keyword"
                    }
                }
            }
        }

        return self.put_request(URL, data)

    def search_item(self, query, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}/_search/?pretty=true&filter_path=-hits.hits._source.text_embedding"
        data_old = {
            "from": 0, "size": 100, 
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, doc['text_embedding']) + 1.0",
                        "params": {
                            "query_vector": e5q_emb_model.embed_query(query).tolist()
                        }
                    }
                }
            }
        }
        data = {
            "_source": {
                "excludes": "text_embedding"
            },
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, doc['text_embedding']) + 1.0",
                        "params": {
                            "query_vector": e5q_emb_model.embed_query(query).tolist()
                        }
                    }
                }
            },
            "sort": [
                {
                    "_score": {
                        "order": "desc"
                    }
                }
            ],
            "size": 10
        }

        return self.post_request(URL, data)

    def create_item(self, id, chunk_text, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}/_doc/"

        data = {
            "text": chunk_text,
            "id": id,
            "text_embedding": e5q_emb_model.embed_query(chunk_text).tolist()
        }

        return self.post_request(URL, data)

"""统一多源搜索 — 一个查询并行搜索所有知识库。"""
import os
from pathlib import Path

# 离线模式，避免 sentence-transformers 直连 huggingface
os.environ["HF_HUB_OFFLINE"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer


# === 初始化 ===

CHROMA_PATH = str(Path(__file__).parent.parent.parent / "AI工程/rag-project/backend/chroma_data")

_client = chromadb.PersistentClient(path=CHROMA_PATH)

# 已知的集合（wiki_knowledge 待后续入库后加入）
KNOWN_COLLECTIONS = ["annual_reports", "agent_engineering", "wiki_knowledge"]

# bge 中文语义模型（384维）
_embed_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5",
    local_files_only=True
)


# === 核心函数 ===

def unified_search(query, top_k=5):
    """并行搜索所有知识库，按相关度合并返回。

    返回格式：
    [
        {"source": "annual_reports", "content": "...", "distance": 0.23},
        {"source": "agent_engineering", "content": "...", "distance": 0.45},
        ...
    ]
    """
    query_vec = _embed_model.encode(query).tolist()
    all_results = []

    for coll_name in KNOWN_COLLECTIONS:
        try:
            collection = _client.get_collection(coll_name)
            results = collection.query(
                query_embeddings=[query_vec],
                n_results=top_k
            )
            # results["documents"][0] 是 top_k 个文档列表
            # results["distances"][0] 是对应的距离列表
            for doc, dist in zip(results["documents"][0], results["distances"][0]):
                all_results.append({
                    "source": coll_name,
                    "content": doc,
                    "distance": round(dist, 4)
                })
        except Exception as e:
            continue  # 集合不存在就跳过

    # 按相关度排序（距离越小越相关）
    all_results.sort(key=lambda x: x["distance"])
    return all_results


def search_formatted(query, top_k=5):
    """搜索并格式化为 Agent 可读的文本。"""
    results = unified_search(query, top_k)
    if not results:
        return "未找到相关知识。"
    
    lines = [f"搜索「{query}」找到 {len(results)} 条结果：\n"]
    for i, r in enumerate(results, 1):
        source_label = {"annual_reports": "年报", "agent_engineering": "Agent工程", "wiki_knowledge": "Wiki"}
        label = source_label.get(r["source"], r["source"])
        lines.append(f"[{i}] 来源：{label}（距离 {r['distance']}）")
        lines.append(f"    {r['content'][:300]}")
        lines.append("")
    
    return "\n".join(lines)

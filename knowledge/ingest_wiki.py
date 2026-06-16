"""Wiki 入库 — 扫描 Wiki 目录 → 分块 → 向量化 → ChromaDB collection wiki_knowledge。"""

from pathlib import Path
import re

from knowledge.search import _client, _embed_model  # 复用已有连接

WIKI_ROOT = Path("/Users/ns/Wiki")
EXCLUDE_DIRS = {"00.配置 Config", ".obsidian", ".git", ".trash"}
COLLECTION_NAME = "wiki_knowledge"


def list_md_files(root):
    """递归收集所有 .md 文件，排除配置目录。"""
    files = []
    for path in root.rglob("*.md"):
        # 跳过排除目录
        parts = set(path.relative_to(root).parts)
        if parts & EXCLUDE_DIRS:
            continue
        files.append(path)
    return sorted(files)


def chunk_by_headers(text, source_path):
    """按 ## 标题分块。没有标题的短文章整体作为一个块。

    Yields: (chunk_text, metadata_dict)
    """
    relative = str(source_path.relative_to(WIKI_ROOT))
    # 匹配二级标题（允许前后空格）
    sections = re.split(r"\n(?=## )", text)

    # 第一个 section 是 ## 之前的部分（如果有内容）
    intro = sections[0].strip()
    if intro:
        yield intro, {"source": relative, "section": "(前言)"}

    for sec in sections[1:]:
        sec = sec.strip()
        if not sec:
            continue
        # 提取标题
        header_match = re.match(r"## (.+)", sec)
        section_title = header_match.group(1).strip() if header_match else "(无标题)"
        yield sec, {"source": relative, "section": section_title}


def ingest():
    """主流程：扫描 → 分块 → 向量化 → 入库。"""
    files = list_md_files(WIKI_ROOT)
    print(f"扫描到 {len(files)} 个 .md 文件")

    # 获取或创建 collection
    coll = _client.get_or_create_collection(COLLECTION_NAME)

    total_chunks = 0
    for fpath in files:
        try:
            text = fpath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  跳过 {fpath.name}：{e}")
            continue

        chunks = list(chunk_by_headers(text, fpath))
        if not chunks:
            continue

        documents = []
        metadatas = []
        ids = []
        for i, (chunk_text, meta) in enumerate(chunks):
            documents.append(chunk_text)
            metadatas.append(meta)
            ids.append(f"{fpath.stem}_{i}")

        # 向量化 + 入库（分批避免内存爆）
        embeddings = _embed_model.encode(documents, show_progress_bar=False).tolist()
        coll.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)

        total_chunks += len(chunks)
        print(f"  {fpath.relative_to(WIKI_ROOT)} → {len(chunks)} 块")

    print(f"\n完成：{len(files)} 文件 → {total_chunks} 块 → collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    ingest()

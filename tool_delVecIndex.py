"""
tool_delVecIndex.py

このスクリプトは、Neo4j データベースに接続し、指定されたベクトルインデックスを削除する機能を提供します。

依存関係:
- neo4j: Neo4j データベースに接続するためのライブラリ
- langchain_community.vectorstores: Neo4jVector クラスを使用するためのライブラリ

使用方法:
1. Neo4j データベースの URI、ユーザー名、およびパスワードを設定します。
2. `delete_vector_index` 関数を呼び出して、指定されたインデックスを削除します。

関数:
- delete_vector_index(index_name: str): 指定された名前のインデックスを削除します。
"""
from neo4j import GraphDatabase
from langchain_community.vectorstores import Neo4jVector

# Neo4j データベースに接続する
uri = "bolt://localhost:7687"
username = "neo4j"
password = "neo4jpass"
driver = GraphDatabase.driver(uri, auth=(username, password))

def delete_vector_index(index_name: str):
    with driver.session() as session:
        session.run(f"DROP INDEX {index_name} IF EXISTS")

# 既存のベクトルインデックスを削除
delete_vector_index("vector")

# # 新しいベクトルインデックスを作成
# vector_index = Neo4jVector.create_new_index(
#     embedding_model=embedding_model,
#     index_name="vector",
#     dimension=384  # embedding_modelの次元に合わせる
# )
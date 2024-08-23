# GraphRAG 検証実装
ナレッジグラフを利用したRAG検索を、Langchainのグラフ機能と、Neo4jグラフデータベースにより検証します 

How to construct knowledge graphs
[https://platform.openai.com/docs/assistants/tools/file-search](https://python.langchain.com/v0.2/docs/how_to/graph_constructing/)

LangChain Neo4j Integration
https://neo4j.com/labs/genai-ecosystem/langchain/

## 概要

このプロジェクトは、Langchain, Neo4j API を使用して、GraphRag アプローチの問い合わせを実行します。具体的には、ユーザーからの質問に対し、Wikipediaの内容をナレッジグラフ化したものを使って、回答を生成します。

## 機能

- ユーザーからの質問に対して、指定テキストファイルの情報の関係グラフを使って回答する

## 確認している必要条件

- Python 3.11 以上
- OpenAI API アクセス情報
- Neo4j Database アクセス情報

## インストール方法

1. このリポジトリをクローンまたはダウンロードします。
2. 必要なライブラリをインストールします。

　　poetryを導入している場合

    ```bash
    poetry poetry install --no-root
    ```

## 使用方法

1. `.env-template` ファイルを元にして、`.env`ファイルを配置します。
2. 必要に応じて、OpenAI, Neo4jのアクセス情報を設定します。
3. スクリプトを実行します。

    ```bash
    python graphsample.py
    ```

4. 一度実行すると、Neo4jにグラフデータが格納され、LLMによるグラフ関係の作成は不要。以下は、Neo4Jデータを使ってRAG実行します。

    ```bash
    python graphRetrieve.py
    ```


## 注意事項

OpenAI API 課金には注意が必要。精度面のこともあるが、試行錯誤は、gpt-4o-mini 利用を推奨します。

Be careful with OpenAI API charges. Although there are accuracy issues, we recommend using gpt-4o-mini for trial and error.

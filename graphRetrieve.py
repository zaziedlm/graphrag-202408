# -*- coding: utf-8 -*-
"""GraphRAG_20240815.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1TTjVFCaGMNSmXCMFnVEobCJflEcP2tlB
"""

# 参考 https://blog.langchain.dev/enhancing-rag-based-applications-accuracy-by-constructing-and-leveraging-knowledge-graphs/

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# %pip install --upgrade --quiet  langchain langchain-community langchain-openai langchain-experimental neo4j wikipedia tiktoken yfiles_jupyter_graphs
# for VSCode poetry environment
# poetry add langchain langchain-community langchain-openai langchain-experimental neo4j wikipedia
# poetry add python-dotenv

import os
from neo4j import GraphDatabase
from yfiles_jupyter_graphs import GraphWidget
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough, ConfigurableField
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
#from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
from typing import List
from langchain_core.output_parsers import StrOutputParser
from langchain_community.graphs import Neo4jGraph
#from langchain.document_loaders import TextLoader  # old import
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import TokenTextSplitter
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from dotenv import load_dotenv

# try:
#     import google.colab
#     from google.colab import output
#     output.enable_custom_widget_manager()
# except:
#     pass

# import getpass

# os.environ["OPENAI_API_KEY"] = getpass.getpass(prompt = 'OpenAIのAPIキーを入力してください')
# os.environ["NEO4J_URI"] = getpass.getpass(prompt = 'NEO4JのURIを入力してください')
# os.environ["NEO4J_USERNAME"] = getpass.getpass(prompt = 'NEO4JのUSERNAMEを入力してください')
# os.environ["NEO4J_PASSWORD"] = getpass.getpass(prompt = 'NEO4Jのパスワードを入力してください')

# read .env file
load_dotenv()

# 
#
#

# raw_documents = TextLoader('ドラゴンボールあらすじ.txt', encoding='utf-8').load()
# text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=125)
# documents = text_splitter.split_documents(raw_documents)

llm=ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
#llm=ChatOpenAI(temperature=0, model_name="gpt-4o")
# llm_transformer = LLMGraphTransformer(llm=llm)
# graph_documents = llm_transformer.convert_to_graph_documents(documents)

graph = Neo4jGraph(
    url = os.environ["NEO4J_URI"],
    username = os.environ["NEO4J_USERNAME"],
    password = os.environ["NEO4J_PASSWORD"]
)

# graph.add_graph_documents(
#     graph_documents,
#     baseEntityLabel=True,
#     include_source=True
# )

# # directly show the graph resulting from the given Cypher query
# default_cypher = "MATCH (s)-[r:!MENTIONS]->(t) RETURN s,r,t LIMIT 50"

# def showGraph(cypher: str = default_cypher):
#     # create a neo4j session to run queries
#     driver = GraphDatabase.driver(
#         uri = os.environ["NEO4J_URI"],
#         auth = (os.environ["NEO4J_USERNAME"],
#                 os.environ["NEO4J_PASSWORD"]))
#     session = driver.session()
#     widget = GraphWidget(graph = session.run(cypher).graph())
#     widget.node_label_mapping = 'id'
#     #display(widget)
#     return widget

# showGraph()



vector_index = Neo4jVector.from_existing_graph(
    OpenAIEmbeddings(),
    search_type="hybrid",
    node_label="Document",
    text_node_properties=["text"],
    embedding_node_property="embedding"
)

# graph.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")

# Extract entities from text
class Entities(BaseModel):
    """Identifying information about entities."""

    names: List[str] = Field(
        ...,
        description="All the person, organization, or business entities that "
        "appear in the text",
    )

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting organization and person entities from the text.",
        ),
        (
            "human",
            "Use the given format to extract information from the following "
            "input: {question}",
        ),
    ]
)

entity_chain = prompt | llm.with_structured_output(Entities)

# entity_chain.invoke({"question": "梧空とにゃんたは戦った"}).names

def generate_full_text_query(input: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2 changed characters) to each word, then combines
    them using the AND operator. Useful for mapping entities from user questions
    to database values, and allows for some misspelings.
    """
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

# Fulltext index query
def structured_retriever(question: str) -> str:
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    result = ""
    entities = entity_chain.invoke({"question": question})
    for entity in entities.names:
        response = graph.query(
            """CALL db.index.fulltext.queryNodes('entity', $query, {limit:20})
            YIELD node,score
            CALL {
              WITH node
              MATCH (node)-[r:!MENTIONS]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
              UNION ALL
              WITH node
              MATCH (node)<-[r:!MENTIONS]-(neighbor)
              RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            }
            RETURN output LIMIT 1000
            """,
            {"query": generate_full_text_query(entity)},
        )
        result += "\n".join([el['output'] for el in response])
    return result

# print(structured_retriever("孫悟空と関わりがあるエンティティを知りたい"))

def retriever(question: str):
    print(f"Search query: {question}")
    structured_data = structured_retriever(question)
    unstructured_data = [el.page_content for el in vector_index.similarity_search(question)]
    final_data = f"""Structured data:
    {structured_data}
    Unstructured data:
    {"#Document ". join(unstructured_data)}
    """
    # print(final_data)
    return final_data

_search_query = RunnableLambda(lambda x: x["question"])

template = """あなたは優秀なAIです。下記のコンテキストを利用してユーザーの質問に丁寧に答えてください。
必ず文脈からわかる情報のみを使用して回答を生成してください。
{context}

ユーザーの質問: {question}"""
prompt = ChatPromptTemplate.from_template(template)

chain = (
    RunnableParallel(
        {
            "context": _search_query | retriever,
            "question": RunnablePassthrough(),
        }
    )
    | prompt
    | llm
    | StrOutputParser()
)

result = chain.invoke({"question": "梧空と仲が良いのは誰"})

print(result)
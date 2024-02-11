import os
from langchain.docstore.document import Document
from langchain.vectorstores.pgvector import PGVector
from langchain_community.embeddings import OpenAIEmbeddings

from dotenv import load_dotenv
from typing import Dict
import pandas as pd
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel

from langchain.schema.output_parser import StrOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

load_dotenv()

class RagChain:
    COLLECTION_NAME = "test3"
    DB_DRIVER_DEFAULT = "psycopg2"
    DB_HOST_DEFAULT = "localhost"
    DB_PORT_DEFAULT = 5432
    DB_NAME_DEFAULT = "postgres"
    DB_USER_DEFAULT = "postgres"

    def __init__(self):
        self.df = pd.read_csv("input/securememo_faq.csv")
        self.con_str = self.create_connection_string()
        self.vector_store = self.initialize_vector_store()

    def create_connection_string(self) -> str:
        driver = os.environ.get("DB_DRIVER", self.DB_DRIVER_DEFAULT)
        host = os.environ.get("DB_HOST", self.DB_HOST_DEFAULT)
        port = int(os.environ.get("DB_PORT", self.DB_PORT_DEFAULT))
        database = os.environ.get("DB_NAME", self.DB_NAME_DEFAULT)
        user = os.environ.get("DB_USER", self.DB_USER_DEFAULT)
        password = os.environ.get("PASSWORD", "")
        return f"postgresql+{driver}://{user}:{password}@{host}:{port}/{database}"

    def initialize_vector_store(self):
        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        documents = [Document(page_content=text) for text in self.df["text"].to_list()]
        return PGVector.from_documents(
            collection_name=self.COLLECTION_NAME,
            connection_string=self.con_str,
            embedding=embedding,
            documents=documents,
            pre_delete_collection=True,
        )

    def answer(self, query: str) -> Dict:
        output_parser = StrOutputParser()
        model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)
        prompt = ChatPromptTemplate.from_template(
            """
            以下のcontextだけに基づいて回答してください。
            {context}
            
            質問: 
            {question}
            """
        )

        rag_chain_from_docs = (
            RunnablePassthrough()
            | prompt
            | model
            | output_parser
        )

        rag_chain_with_source = RunnableParallel(
            {"context": self.vector_store.as_retriever(search_kwargs={"k": 3}), "question": RunnablePassthrough()}
        ).assign(answer=rag_chain_from_docs)
        return rag_chain_with_source.invoke(query)
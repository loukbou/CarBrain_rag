#Handles chunking, embeddings (using all-MiniLM-L6-v2), and FAISS vector storage.

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from typing import List

class RAGProcessor:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def process_documents(self, documents: List[Document]) -> FAISS:
        """Split, embed, and store documents."""
        chunks = self.text_splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        return vectorstore

    def query(self, vectorstore: FAISS, question: str, k=3) -> List[Document]:
        """Retrieve relevant chunks."""
        return vectorstore.similarity_search(question, k=k)
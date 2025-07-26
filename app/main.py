#FastAPI Backend
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from document_loader import load_pdf_with_tables_images, load_docx_with_tables, load_csv_autoparts, load_pptx_slides
from rag_processor import RAGProcessor
import os

app = FastAPI()
rag = RAGProcessor()

class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(request: QueryRequest):
    try:
        docs = rag.query(vectorstore, request.question)
        return {"answer": docs[0].page_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
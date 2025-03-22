
from typing import List, Dict
import anthropic

ANTHROPIC_API_KEY = "REPLACE ME"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""

    chunks = []
    sentences = text.split('. ') 
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip() + '. '
        sentence_length = len(sentence)
        
        if current_length + sentence_length > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            overlap_text = ' '.join(current_chunk[-2:])
            current_chunk = [overlap_text]
            current_length = len(overlap_text)
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SimpleRag():
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_store = {
            'embeddings': [],
            'sources': [],
            'chunks': []
        }

    def _add_to_store(self, file: str):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        chunks = chunk_text(content)        
        embeddings = self.encoder.encode(chunks)
        self.vector_store['embeddings'].extend(embeddings)
        self.vector_store['sources'].extend([file] * len(chunks))
        self.vector_store['chunks'].extend(chunks)

    def retrieve_context(self, q: str, k: str):
        question_embedding = self.encoder.encode([q])[0]
        similarities = cosine_similarity([question_embedding], self.vector_store['embeddings'])[0]
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        results = []
        for idx in top_k_indices:
            results.append({
                'source': self.vector_store['sources'][idx],
                'content': self.vector_store['chunks'][idx],
                'similarity': similarities[idx]
            })
        return results

    def make_prompt(self, q: str, ctxs: list[str]):
        prompt = f"Question: {q}\n\nContext:\n"
        for ctx in ctxs:
            prompt += f"{ctx['source']}: {ctx['content']}\n"
        return prompt
    
    def query(self, q: str):
        ctxs = self.retrieve_context(q, 2)
        prompt = self.make_prompt(q, ctxs)
        sys_prompt = "You are intelligent QA bot, who is very good at providing concise ans. Don't preamble. Just Ans."
        resp = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=2000,
            temperature=0.0,
            system=sys_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text

rag = SimpleRag()
rag._add_to_store("docs/example.txt")

query = "Who directed movie Mickey 17, and what is it about?"
rag.query(query)

import base64
import json
from utils import visualize_citations

pdf_path = 'docs/2024ltr.pdf' # fill me
with open(pdf_path, "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode()

pdf_response = client.messages.create(
    model="claude-3-5-sonnet-latest",
    temperature=0.0,
    max_tokens=4000,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    },
                    "title": "BERKSHIRE HATHAWAY INC. 2024 Letter",
                    "citations": {"enabled": True}
                },
                {
                    "type": "text",
                    "text": "How many bizs reported decline in earnings?"
                }
            ]
        }
    ]
)

print(visualize_citations(pdf_response))
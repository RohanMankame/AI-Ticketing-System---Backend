import os
import json
import numpy as np
from openai import OpenAI
from openai import OpenAI
from models.ticket import Ticket
from models.knowledge import KnowledgeArticle
from extensions import db

class AIService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                # Fallback for dev/test if key not present, or raise error
                print("Warning: OPENAI_API_KEY not set.")
                return None
            cls._client = OpenAI(api_key=api_key)
        return cls._client

    @staticmethod
    def generate_embedding(text):
        client = AIService.get_client()
        if not client or not text:
            return None
        
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    @staticmethod
    def classify_ticket(ticket_summary):
        client = AIService.get_client()
        if not client or not ticket_summary:
            return None

        prompt = f"""
        Analyze the following support ticket summary and extract:
        1. A comprehensive category (e.g., "Login Issue", "Database Error", "UI Glitch").
        2. A list of 3-5 keywords/tags.
        3. A sentiment score from -1.0 (very negative) to 1.0 (very positive).

        Ticket Summary: "{ticket_summary}"

        Return ONLY a valid JSON object with keys: "category", "tags", "sentiment".
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for a support ticketing system."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Error classifying ticket: {e}")
            return None

    @staticmethod
    def find_similar_tickets(ticket_id, top_k=3):
        target_ticket = Ticket.query.get(ticket_id)
        if not target_ticket or not target_ticket.embedding:
            return []

        target_emb = np.array(json.loads(target_ticket.embedding))
        
        # Fetch all other tickets with embeddings 
        all_tickets = Ticket.query.filter(Ticket.id != ticket_id, Ticket.embedding != None).all()
        
        similarities = []
        for t in all_tickets:
            emb = np.array(json.loads(t.embedding))
            # Cosine similarity
            score = np.dot(target_emb, emb) / (np.linalg.norm(target_emb) * np.linalg.norm(emb))
            similarities.append((score, t))
        
        # Sort by score desc
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        return [{"score": float(s[0]), "ticket": s[1].to_dict()} for s in similarities[:top_k]]

    @staticmethod
    def suggest_solution(ticket_id):
        client = AIService.get_client()
        if not client:
            return None

        target_ticket = Ticket.query.get(ticket_id)
        if not target_ticket:
            return None

        similar_tickets = AIService.find_similar_tickets(ticket_id, top_k=3)
        
        context_str = ""
        for item in similar_tickets:
            t = item['ticket']
            context_str += f"- Issue: {t['summary']}\n  Resolution: {t.get('resolution', 'None')}\n\n"

        prompt = f"""
        I have a new support ticket:
        Summary: "{target_ticket.summary}"
        Description: "{target_ticket.summary}" (Using summary as description for now)

        Here are similar past tickets and their resolutions:
        {context_str}

        Based on this, suggest a solution for the new ticket. 
        Also provide a list of relevant documentation links if you can infer any generic ones (e.g. "Check Database Config Docs").
        Return JSON with keys: "suggested_solution", "relevant_links".
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical support expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error suggesting solution: {e}")
            return None

    @staticmethod
    def find_relevant_knowledge(query_text, top_k=3):
        client = AIService.get_client()
        if not client or not query_text:
            return []

        query_emb = AIService.generate_embedding(query_text)
        if not query_emb:
            return []

        target_emb = np.array(query_emb)
        
        # Fetch knowledge articles with embeddings
        articles = KnowledgeArticle.query.filter(KnowledgeArticle.embedding != None).all()
        
        similarities = []
        for a in articles:
            emb = np.array(json.loads(a.embedding))
            score = np.dot(target_emb, emb) / (np.linalg.norm(target_emb) * np.linalg.norm(emb))
            similarities.append((score, a))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        return [{"score": float(s[0]), "article": s[1].to_dict()} for s in similarities[:top_k]]

    @staticmethod
    def draft_article_from_tickets(ticket_ids):
        client = AIService.get_client()
        if not client:
            return None

        tickets = Ticket.query.filter(Ticket.id.in_(ticket_ids)).all()
        if not tickets:
            return None

        context = ""
        for t in tickets:
            context += f"- Issue: {t.summary}\n  Resolution: {t.resolution}\n  Sentiment: {t.sentiment_score}\n\n"

        prompt = f"""
        Based on the following resolved support tickets, draft a new Knowledge Base Article.
        The article should include a Title, a comprehensive Body (explaining the issue and solution), and tags.
        
        Tickets:
        {context}

        Return JSON with keys: "title", "content", "tags" (list of strings).
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical document writer."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error drafting article: {e}")
            return None

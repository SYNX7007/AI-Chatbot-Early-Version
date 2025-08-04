import httpx
import os
import json
from typing import List, Dict
from sqlalchemy.orm import Session
import models

class PerplexityClient:

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def generate_response(
        self,
        prompt: str,
        department: str,
        user_id: int,
        db: Session,
        model: str = "sonar-pro"
    ) -> Dict:
        """Generate AI response using Perplexity API with department context."""

        # Get department context
        dept = db.query(models.Department).filter(
            models.Department.key == department
        ).first()

        if not dept:
            raise ValueError("Department not found")

        # Construct system message with department context - use a single string without extra indentation
        system_message = (
            f"{dept.ai_context}\n"
            f"Company: {os.getenv('COMPANY_NAME', 'Ankit Solutions')}\n"
            f"Department: {dept.name}\n"
            "Important guidelines:\n"
            "- Only answer questions related to company operations and this department\n"
            "- Use professional language appropriate for internal company communication\n"
            "- If asked about non-company topics, politely redirect to company-related matters\n"
            "- Base responses on current information and best practices\n"
            "- Be helpful but maintain confidentiality of sensitive information\n"
        )

        payload = {
            "model": "sonar",  # or "sonar-pro" but only if your account supports it!
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7,
            "return_citations": True
        }


        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()

            data = response.json()

            ai_response = data["choices"][0]["message"]["content"]

            # Extract citations if available
            citations = []
            if "search_results" in data:
                citations = [
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", "")
                    }
                    for result in data["search_results"][:5]  # Limit to top 5
                ]

            # Save conversation to database
            self._save_conversation(db, user_id, department, prompt, ai_response, citations)

            return {
                "response": ai_response,
                "citations": citations,
                "model": model
            }

        except httpx.HTTPStatusError as e:
            print(f"Perplexity API error: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again later or contact your system administrator.",
                "citations": [],
                "model": model
            }

    def _save_conversation(
        self,
        db: Session,
        user_id: int,
        department: str,
        user_message: str,
        ai_response: str,
        citations: List[Dict]
    ):
        """Save conversation to database."""
        conversation = models.Conversation(
            user_id=user_id,
            department=department,
            user_message=user_message,
            ai_response=ai_response,
            citations=json.dumps(citations)  # Store citations as JSON string
        )
        db.add(conversation)
        db.commit()

def is_prompt_allowed(prompt: str, department_blocked_keywords: List[str]) -> bool:
    """Check if the prompt is company-related and allowed."""
    prompt_lower = prompt.lower()

    # Global blocked keywords
    global_blocked = [
        "game of the year", "entertainment", "movies", "sports",
        "personal life", "dating", "weather", "celebrity", "gaming",
        "what is the weather", "tell me a joke", "movie recommendations"
    ]

    # Check global and department-specific blocked keywords
    all_blocked = global_blocked + (department_blocked_keywords or [])

    for keyword in all_blocked:
        if keyword.lower() in prompt_lower:
            return False

    # Check for company-related keywords
    company_keywords = [
        "budget", "finance", "tax", "policy", "procedure",
        "compliance", "employee", "department", "company",
        "revenue", "expense", "regulation", "audit", "business"
    ]

    has_company_context = any(keyword in prompt_lower for keyword in company_keywords)
    return has_company_context

# Initialize Perplexity client instance
perplexity_client = PerplexityClient()

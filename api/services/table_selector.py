import json
import os
from pydantic import BaseModel, Field
from openai import OpenAI
from api.services.schema_context import get_schema_catalog

class TableSelection(BaseModel):
    selected_tables: list[str] = Field(
        description="List of table names required to answer the user's question."
    )

def select_tables_for_query(question: str) -> list[str]:
    """
    Uses a fast, cheap model to determine which tables are needed for the query.
    Returns a list of table names.
    """
    catalog = get_schema_catalog()
    
    # If the catalog is tiny, we might just return everything, but assuming it's growing:
    catalog_str = json.dumps(catalog, indent=2)
    
    system_prompt = f"""
    You are an expert data architect. Your job is to select the minimum necessary database tables 
    to answer the user's question.
    
    Here is the data warehouse catalog (Table Name -> Description):
    {catalog_str}
    
    Rules:
    1. Select ONLY the tables strictly necessary to answer the question.
    2. If the user asks for a specific metric (e.g., sales, refunds), pick the table that serves that metric.
    3. If no tables are relevant (e.g., it's a pure customer support complaint question), return an empty list.
    """

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Using 4o-mini for speed and cost efficiency
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        response_format=TableSelection,
        temperature=0.0 # Keep it deterministic
    )
    
    return response.choices[0].message.parsed.selected_tables
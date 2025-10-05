#!/usr/bin/env python3
"""
Alternatywna metoda - używamy Railway GraphQL API bezpośrednio
"""

import requests
import json

# Railway GraphQL endpoint
API_URL = "https://backboard.railway.com/graphql/v2"

# Zapytania GraphQL
QUERIES = {
    "create_project": """
        mutation {
          projectCreate(input: { name: "btc-trading-system" }) {
            id
            name
          }
        }
    """,
    "list_projects": """
        query {
          projects {
            edges {
              node {
                id
                name
                createdAt
              }
            }
          }
        }
    """
}

def call_railway_api(query, token):
    """Call Railway API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        API_URL,
        headers=headers,
        json={"query": query}
    )
    
    return response.json()

# Próba z różnymi tokenami
tokens_to_try = [
    "3eff650a-c1ef-44a0-8b04-538ecba70f7b",  # Podany token
]

print("🔍 Testowanie Railway API...")
print()

for token in tokens_to_try:
    print(f"Próba z tokenem: {token[:20]}...")
    result = call_railway_api(QUERIES["list_projects"], token)
    print(json.dumps(result, indent=2))
    print()


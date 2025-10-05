#!/usr/bin/env python3
"""
Automatyczny deployment na Railway przez GraphQL API
"""

import requests
import json
import time

API_URL = "https://backboard.railway.com/graphql/v2"
TOKEN = "3eff650a-c1ef-44a0-8b04-538ecba70f7b"

def call_api(query, variables=None):
    """Call Railway GraphQL API"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

print("🚀 AUTOMATYCZNY DEPLOYMENT NA RAILWAY")
print("=" * 50)
print()

# 1. Utwórz nowy projekt
print("📦 Krok 1: Tworzenie projektu 'btc-trading-system'...")
create_project = """
mutation($name: String!) {
  projectCreate(input: { name: $name }) {
    id
    name
  }
}
"""

result = call_api(create_project, {"name": "btc-trading-system"})
if "errors" in result:
    print(f"   ⚠️  Błąd (może już istnieć): {result['errors'][0]['message']}")
    # Spróbuj użyć istniejącego projektu
    list_query = """
    query {
      projects {
        edges {
          node {
            id
            name
          }
        }
      }
    }
    """
    projects = call_api(list_query)
    project_id = projects['data']['projects']['edges'][0]['node']['id']
    project_name = projects['data']['projects']['edges'][0]['node']['name']
    print(f"   ✓ Używam istniejącego projektu: {project_name}")
else:
    project_id = result['data']['projectCreate']['id']
    print(f"   ✓ Projekt utworzony: {project_id}")

print()

# 2. Dodaj PostgreSQL
print("🗄️  Krok 2: Dodawanie PostgreSQL...")
add_postgres = """
mutation($projectId: String!) {
  pluginCreate(input: { 
    projectId: $projectId,
    name: "postgresql"
  }) {
    id
  }
}
"""

result = call_api(add_postgres, {"projectId": project_id})
if "errors" in result:
    print(f"   ⚠️  {result['errors'][0]['message']}")
else:
    print(f"   ✓ PostgreSQL dodany")

time.sleep(2)
print()

# 3. Dodaj Redis
print("💾 Krok 3: Dodawanie Redis...")
add_redis = """
mutation($projectId: String!) {
  pluginCreate(input: { 
    projectId: $projectId,
    name: "redis"
  }) {
    id
  }
}
"""

result = call_api(add_redis, {"projectId": project_id})
if "errors" in result:
    print(f"   ⚠️  {result['errors'][0]['message']}")
else:
    print(f"   ✓ Redis dodany")

print()

# 4. Sprawdź status
print("📊 Krok 4: Sprawdzanie statusu projektu...")
status_query = """
query($projectId: String!) {
  project(id: $projectId) {
    id
    name
    services {
      edges {
        node {
          id
          name
        }
      }
    }
    plugins {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
"""

result = call_api(status_query, {"projectId": project_id})
if "data" in result and result["data"]["project"]:
    project = result["data"]["project"]
    print(f"   ✓ Projekt: {project['name']}")
    print(f"   ✓ ID: {project['id']}")
    
    if project.get('plugins', {}).get('edges'):
        print(f"   ✓ Plugins: {len(project['plugins']['edges'])} zainstalowanych")
        for plugin in project['plugins']['edges']:
            print(f"      - {plugin['node']['name']}")
    
    if project.get('services', {}).get('edges'):
        print(f"   ✓ Services: {len(project['services']['edges'])}")

print()
print("=" * 50)
print("✅ Podstawowy setup zakończony!")
print()
print("📝 Następne kroki (ręcznie w terminalu):")
print("   1. railway link - połącz z projektem")
print("   2. cd services/data-validation")
print("   3. railway up - deploy serwis")
print()
print(f"🌐 Dashboard: https://railway.app/project/{project_id}")
print()


"""
Script de test pour l'outil de recherche web.
"""
from tools.search import search_web

def test_search():
    print("=" * 60)
    print("TEST: Recherche web avec DuckDuckGo")
    print("=" * 60)
    
    query = "actualités technologie 2024"
    print(f"\nRecherche: '{query}'\n")
    
    result = search_web(query, max_results=3)
    print(result)
    
    if "Error" in result:
        print("\n❌ ÉCHEC: Erreur lors de la recherche")
    else:
        print("\n✅ SUCCÈS: Recherche effectuée avec succès")

if __name__ == "__main__":
    test_search()

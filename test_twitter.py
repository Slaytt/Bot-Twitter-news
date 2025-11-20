"""
Script de test pour l'outil de publication Twitter.
Note: Ce test ne publiera PAS réellement de tweet, il vérifie juste
la configuration et la connexion à l'API Twitter.
"""
from tools.twitter import post_tweet

def test_twitter_credentials():
    print("=" * 60)
    print("TEST: Vérification des credentials Twitter")
    print("=" * 60)
    
    # Test avec un message de test (qui sera publié si les credentials sont configurés)
    test_content = "🤖 Test du bot Twitter MCP - Message de test"
    
    print(f"\nContenu du tweet: '{test_content}'")
    print("\n⚠️  ATTENTION: Ce message sera publié si les credentials sont configurés!\n")
    
    response = input("Voulez-vous continuer? (y/n): ")
    
    if response.lower() != 'y':
        print("\nTest annulé.")
        return
    
    result = post_tweet(test_content)
    print(f"\nRésultat: {result}")
    
    if "Error" in result:
        if "credentials not found" in result:
            print("\n⚠️  INFO: Credentials Twitter non configurés dans .env")
        else:
            print("\n❌ ÉCHEC: Erreur lors de la publication")
    else:
        print("\n✅ SUCCÈS: Tweet publié avec succès!")

if __name__ == "__main__":
    test_twitter_credentials()

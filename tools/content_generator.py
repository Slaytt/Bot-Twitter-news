import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def generate_tweet_content(topic: str, source_content: str = None, tone: str = "professional") -> str:
    """
    Génère un tweet sur un sujet donné en utilisant l'API Gemini.
    
    Args:
        topic: Le sujet du tweet.
        source_content: Contenu optionnel pour donner du contexte (ex: article scrapé).
        tone: Le ton du tweet (ex: professionnel, humoristique, enthousiaste).
        
    Returns:
        Le contenu du tweet généré ou un message d'erreur.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in .env file."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        # Framework de tweet tech viral 2025
        prompt = f"""
🔥 RÔLE : Tu es un expert Tech/IA influent sur Twitter France. Ton but est d'informer et d'engager ta communauté avec des analyses pertinentes et percutantes.

📰 CONTEXTE (ARTICLE SOURCE) :
{source_content[:3000] if source_content else topic}

🎯 OBJECTIF :
Rédige un tweet captivant sur ce sujet. Il doit être informatif, précis, et donner envie de réagir, sans tomber dans le clickbait bas de gamme.

⚡ RÈGLES D'OR :
1. **Varies les structures** : Ne commence pas toujours par une emoji ou une phrase choc standard. Pose une question, donne un fait brut, ou partage une opinion tranchée.
2. **Sois précis** : Utilise les chiffres, noms et détails techniques présents dans le texte source. Pas de généralités.
3. **Ton naturel et engageant** : Écris comme un humain passionné, pas comme un robot marketing. Utilise l'humour ou l'ironie avec parcimonie mais efficacité.
4. **Pas de répétitions** : Évite les formules toutes faites comme "Pendant ce temps l'Europe..." ou "Révolution ou arnaque ?" à chaque fois.
5. **Longueur** : Utilise l'espace nécessaire pour donner de la valeur (max 280 caractères).

🎨 TON : {tone}

STRUCTURES POSSIBLES (à varier) :
- **L'analyse** : Fait + Conséquence + Question ouverte.
- **Le comparatif** : Avant vs Maintenant (ou US vs FR, mais subtil).
- **Le "Saviez-vous"** : Un détail technique méconnu et fascinant.
- **L'opinion** : Une prise de position forte sur l'actu.

Exemple de bon tweet (structure variable) :
"355 milliards de paramètres pour le nouveau GLM-4.5 de Zhipu AI. 🤯
Il surpasse GPT-4 sur plusieurs benchmarks clés. La Chine ne rattrape pas son retard, elle est en train de passer devant sur l'open source.
On teste ça quand ?"

TA MISSION :
Génère UN seul tweet sur "{topic}".
"""

        response = model.generate_content(prompt)
        tweet = response.text.strip()
        
        # Nettoyer le tweet (enlever les guillemets si l'IA en a mis)
        tweet = tweet.strip('"').strip("'").strip()
        
        return tweet
    except Exception as e:
        return f"Error generating content: {str(e)}"

if __name__ == "__main__":
    # Test rapide (nécessite une clé API valide)
    print(generate_tweet_content("Zhipu AI défie GPT-4 avec GLM-4.5", tone="enthousiaste"))

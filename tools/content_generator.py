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

        # Framework de tweet viral
        prompt = f"""
🎯 RÔLE : Tu es un éditorialiste Twitter cynique et viral. Ton objectif : faire arrêter le scroll.

📰 ARTICLE À TRANSFORMER :
{source_content[:2500] if source_content else topic}

🎨 TON : {tone}

📋 FRAMEWORK DE CRÉATION (APPLIQUE CES 4 RÈGLES) :

1. PATTERN INTERRUPT (L'Arrêt sur Image)
   ❌ INTERDIT : "Aujourd'hui...", "Une nouvelle étude...", "Découvrez...", "Voici..."
   ✅ COMMENCE PAR :
   - Une opinion tranchée
   - Un fait absurde tiré de l'article
   - Une question rhétorique provocante
   - Un chiffre fou
   
2. CURIOSITY GAP (Le Fossé de Curiosité)
   - Repère le CHIFFRE le plus fou ou la CITATION la plus polémique
   - Tease-le sans TOUT dévoiler
   - Donne le "quoi", cache le "comment"
   
3. ÉMOTION (Ton Marrant/Cynique)
   - Utilise l'ironie ou l'exagération
   - Adopte le ton d'un ami blasé qui n'en revient pas
   - Sois sarcastique sur les conséquences
   
4. MISE EN FORME
   - MAXIMUM 280 caractères (STRICT)
   - Utilise des sauts de ligne pour aérer
   - 1-2 emojis MAX (placés stratégiquement, PAS en fin)
   - PAS de hashtags

📝 EXEMPLE CONCRET :

❌ MAUVAIS :
"Apple sort un nouveau casque VR à 3500$. En savoir plus."

✅ BON :
"3 500 $ pour regarder des films tout seul ? 💸

Apple vient de se surpasser avec un casque que personne ne pourra s'offrir.

Les specs qui justifient ce prix (ou pas) 👇"

🎯 TA MISSION :
Crée UN SEUL tweet viral sur "{topic}" en suivant le framework ci-dessus.

⚠️ CONTRAINTES ABSOLUES :
- Moins de 280 caractères
- Pas de hashtags
- Commence par un Pattern Interrupt
- Utilise le Curiosity Gap
- Ton ironique/cynique
- Réponds UNIQUEMENT avec le tweet, rien d'autre
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
    print(generate_tweet_content("L'intelligence artificielle en 2024", tone="enthousiaste"))

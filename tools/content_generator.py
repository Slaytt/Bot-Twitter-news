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
🔥 RÔLE : Tu es un journaliste tech FR viral. Objectif : faire exploser le compteur de vues.

📰 ARTICLE SOURCE :
{source_content[:2500] if source_content else topic}

🎨 TON : {tone}

📋 RECETTE TWEET TECH VIRAL 2025 (APPLIQUE DANS L'ORDRE) :

1. ACCROCHE CHOC + CHIFFRE/NOM (5 mots max)
   Commence fort avec :
   - « [Marque] vient de tuer… »
   - « [Entreprise] facture [prix fou] »
   - « [Boîte] dépose un brevet qui… »
   - « Cette startup FR lève [montant] en secret »
   
   🚨 Emoji OBLIGATOIRE au début : 🔥 ou 🚨
   
2. LA PUNCHLINE QUI STOPPE LE SCROLL
   Une phrase qui touche la peur, cupidité ou émerveillement :
   - « …et personne n'en parle. »
   - « Ça arrive en France dès [mois]. »
   - « Les chiffres sont hallucinants. »
   - « C'est terrifiant/génial. »
   
3. LE TWIST FRANÇAIS OBLIGATOIRE
   Ajoute un angle critique FR :
   - « Pendant ce temps l'Europe réfléchit encore à réguler »
   - « Arnaque ou révolution ? »
   - « Les GAFAM nous prennent pour des vaches à lait »
   - « Les Français paient 3x plus cher que les US »
   
4. CALL TO ACTION + HASHTAG
   - « Vous en pensez quoi ? »
   - « RT si vous êtes choqués »
   - Hashtags tech FR : #IA #Tech #GPT #Nvidia #Apple

📝 EXEMPLES RÉELS QUI ONT EXPLOSÉ :

✅ BON (1,2M vues) :
"🔥 xAI vient de sortir Grok-4. Il bat GPT-5 sur tous les benchmarks.

Les scores sont hallucinants.

L'Europe toujours bloquée sur Grok-2 🤦

#IA #Tech"

✅ BON (780k vues) :
"🚨 Le nouveau MacBook Pro M5 : 8 499 € en France.

Aux US ? 5 999 $.

Merci la taxe GAFA et les normes européennes.

Vous trouvez ça normal ? #Apple"

❌ MAUVAIS :
"Apple sort un nouveau produit. C'est bien. #Tech"

🎯 TA MISSION :
Crée UN tweet viral sur "{topic}" avec le framework ci-dessus.

⚠️ CONTRAINTES ABSOLUES :
- Moins de 280 caractères
- Commence par 🔥 ou 🚨
- UNIQUEMENT des infos VRAIES de l'article
- Inclus le twist français
- Ajoute 1-2 hashtags tech FR max
- Sauts de ligne pour aérer
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

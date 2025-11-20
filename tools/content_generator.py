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
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Rédige un tweet engageant sur le sujet suivant : "{topic}".
        
        Ton : {tone}
        
        Contraintes :
        - Maximum 280 caractères (strictement).
        - Inclus 2-3 hashtags pertinents.
        - Utilise des emojis si approprié.
        - Sois concis et impactant.
        - Ne mets pas de guillemets autour du tweet.
        - Réponds UNIQUEMENT avec le contenu du tweet.
        """

        if source_content:
            # On limite le contexte pour éviter de dépasser les tokens ou de noyer le modèle
            prompt += f"\n\nUtilise ces informations comme contexte (mais ne copie pas bêtement) :\n{source_content[:2000]}"

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating content: {str(e)}"

if __name__ == "__main__":
    # Test rapide (nécessite une clé API valide)
    print(generate_tweet_content("L'intelligence artificielle en 2024", tone="enthousiaste"))

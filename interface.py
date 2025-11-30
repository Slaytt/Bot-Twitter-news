import streamlit as st
import asyncio
from datetime import datetime, timedelta
from tools.scraper import scrape_website
from tools.scraper import scrape_website
from tools.content_generator import generate_tweet_content
from tools.twitter import post_tweet
import database
from database import (
    init_db, get_monthly_count, add_scheduled_tweet, get_all_pending_tweets, 
    delete_scheduled_tweet, get_active_topics, add_monitored_topic, 
    delete_scheduled_tweet, get_active_topics, add_monitored_topic, 
    delete_scheduled_tweet, get_active_topics, add_monitored_topic, 
    delete_monitored_topic, load_fixed_topics
)
from monitoring_service import run_monitoring_cycle

# Ensure DB is initialized
init_db()

st.set_page_config(page_title="Twitter Bot Manager", page_icon="🤖", layout="wide")

st.title("🤖 Twitter Bot Manager")

# Sidebar Navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Générateur de Tweets", "✅ Validation", "File d'attente", "🏆 Top Tweets", "Activité de veille", "Veille Automatique"])

# --- SIDEBAR OPTIONS ---
st.sidebar.markdown("---")
from database import get_setting, set_setting

# Charger l'état depuis la DB
current_pause_state = get_setting("pause_mode", "False") == "True"
pause_mode = st.sidebar.checkbox("⏸️ PAUSE GÉNÉRALE", value=current_pause_state, help="Si coché, aucun tweet ne sera envoyé par le planificateur.")

if pause_mode != current_pause_state:
    set_setting("pause_mode", str(pause_mode))
    st.rerun()

if pause_mode:
    st.sidebar.warning("⚠️ Mode PAUSE activé")

# --- DASHBOARD ---
if page == "Dashboard":
    st.header("Tableau de bord")
    
    if pause_mode:
        st.error("⚠️ LE BOT EST EN PAUSE. Aucun envoi ne sera effectué.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        count = get_monthly_count()
        limit = 500
        st.metric("Tweets envoyés ce mois", f"{count} / {limit}", delta=limit-count, delta_color="normal")
        st.progress(count / limit)
        
    with col2:
        pending = len(get_all_pending_tweets())
        st.metric("Tweets en attente", pending)

    # Zone de Test Configuration
    with st.expander("🛠️ Test Configuration (Debug)"):
        st.info("Utilisez ce bouton pour tester l'envoi d'un tweet EN DIRECT (sans passer par la file d'attente).")
        test_msg = st.text_input("Message de test", value=f"Hello World from Bot! {datetime.now().strftime('%H:%M:%S')}")
        if st.button("Envoyer Tweet Test (Sync)"):
            with st.spinner("Envoi en cours..."):
                res = post_tweet(test_msg)
                if "Error" in res:
                    st.error(f"❌ Échec : {res}")
                else:
                    st.success(f"✅ Succès : {res}")

# --- GENERATOR ---
elif page == "Générateur de Tweets":
    st.header("✍️ Générateur de Tweets")
    
    with st.form("generator_form"):
        topic = st.text_input("Sujet du tweet")
        url = st.text_input("URL source (optionnel)")
        tone = st.select_slider("Ton", options=["informatif", "professionnel", "enthousiaste", "humoristique", "polémique"], value="professionnel")
        
        generate_btn = st.form_submit_button("Générer le tweet")
        
    if generate_btn and topic:
        with st.spinner("Génération en cours..."):
            context = ""
            if url:
                try:
                    # Utilisation d'une nouvelle boucle d'événements pour éviter les conflits
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    context = loop.run_until_complete(scrape_website(url))
                    loop.close()
                except Exception as e:
                    st.error(f"Erreur scraping: {e}")
            
            tweet = generate_tweet_content(topic, source_content=context, tone=tone)
            st.session_state['generated_tweet'] = tweet
            
    if 'generated_tweet' in st.session_state:
        st.subheader("Prévisualisation")
        edited_tweet = st.text_area("Modifier le tweet", value=st.session_state['generated_tweet'], height=150)
        st.caption(f"Caractères: {len(edited_tweet)} / 25000")
        
        if len(edited_tweet) > 25000:
            st.warning("Attention : Le tweet dépasse 25000 caractères !")
            
        col1, col2 = st.columns(2)
        with col1:
            schedule_date = st.date_input("Date d'envoi", value=datetime.now())
        with col2:
            schedule_time = st.time_input("Heure d'envoi", value=datetime.now())
        
        if st.button("Planifier l'envoi", type="primary"):
            run_at = datetime.combine(schedule_date, schedule_time)
            add_scheduled_tweet(edited_tweet, run_at)
            st.success(f"Tweet planifié pour le {run_at} (en attente de validation) !")
            st.session_state.tweet_preview = None
            st.rerun()

# --- VALIDATION ---
elif page == "✅ Validation":
    st.header("✅ Validation des Tweets")
    
    from database import get_tweets_awaiting_approval, approve_tweet, reject_tweet, update_tweet_content, update_tweet_image, update_tweet_thread_content
    from duckduckgo_search import DDGS
    
    awaiting = get_tweets_awaiting_approval()
    
    if not awaiting:
        st.success("🎉 Aucun tweet en attente de validation !")
    else:
        st.write(f"**{len(awaiting)} tweet(s) en attente de validation**")
        
        for tweet in awaiting:
            with st.container():
                st.markdown("---")
                
                col_img, col_content = st.columns([1, 2])
                
                # Colonne Image (Éditable)
                with col_img:
                    # Récupérer l'image actuelle (DB) et celle en cours d'édition (Session State)
                    db_img = tweet.get('image_url', '')
                    img_key = f"img_{tweet['id']}"
                    
                    # Si l'utilisateur a modifié le champ, on utilise la nouvelle valeur pour la preview
                    preview_img = st.session_state.get(img_key, db_img)
                    
                    if preview_img:
                        try:
                            st.image(preview_img, use_container_width=True)
                        except:
                            st.warning(f"Image invalide")
                    else:
                        st.info("Pas d'image")
                    
                    # Champ d'édition d'image
                    new_img_url = st.text_input("URL Image", value=db_img, key=img_key)
                    
                    # Recherche d'image rapide (Bulldozer Method)
                    with st.expander("🔍 Chercher une image"):
                        search_query = st.text_input("Mots-clés ou URL", value=tweet.get('source_url', '') or "Tech News", key=f"search_{tweet['id']}")
                        
                        if st.button("Chercher / Extraire", key=f"btn_search_{tweet['id']}"):
                            # Si c'est une URL Google Images ou autre, on essaie d'extraire
                            if "http" in search_query:
                                import re
                                from urllib.parse import unquote
                                
                                # Cas Google Images : extraire imgurl
                                if "google.com/imgres" in search_query:
                                    match = re.search(r'imgurl=(.*?)(&|$)', search_query)
                                    if match:
                                        extracted_url = unquote(match.group(1))
                                        st.success("Image extraite du lien Google !")
                                        st.image(extracted_url, width=300)
                                        st.code(extracted_url, language=None)
                                        # Proposer de l'appliquer directement
                                        if st.button("Utiliser cette image", key=f"use_extracted_{tweet['id']}"):
                                            update_tweet_image(tweet['id'], extracted_url)
                                            st.rerun()
                                    else:
                                        st.warning("Impossible d'extraire l'image du lien Google.")
                                else:
                                    # C'est peut-être une URL d'image directe
                                    st.image(search_query, width=300)
                                    st.code(search_query, language=None)
                            
                            else:
                                # Recherche normale par mots-clés
                                try:
                                    import asyncio
                                    from tools.search import search_images_playwright
                                    
                                    with st.spinner("Recherche d'images (Bulldozer Mode)..."):
                                        # Utiliser asyncio pour appeler la fonction asynchrone
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        results = loop.run_until_complete(search_images_playwright(search_query, max_results=3))
                                        loop.close()
                                        
                                        if results:
                                            for res in results:
                                                st.image(res['image'], width=150)
                                                st.code(res['image'], language=None)
                                        else:
                                            st.warning("Aucune image trouvée.")
                                            
                                except Exception as e:
                                    st.error(f"Erreur recherche : {str(e)}")

                # Colonne Contenu (Éditable)
                with col_content:
                    st.caption(f"📅 Programmé pour : {tweet['scheduled_time']}")
                    if tweet.get('source_url'):
                        st.caption(f"🔗 Source : {tweet['source_url']}")
                        
                    # Zone d'édition
                    # On calcule d'abord pour afficher l'info AVANT la zone de texte (plus visible)
                    current_content_val = st.session_state.get(f"edit_{tweet['id']}", tweet['content'])
                    chars = len(current_content_val)
                    
                    import re
                    urls = re.findall(r'https?://\S+', current_content_val)
                    will_thread = False
                    
                    if chars > 280 and urls:
                        link = urls[-1]
                        content_without_link = current_content_val.replace(link, "").strip()
                        if len(content_without_link) <= 280:
                            will_thread = True
                    
                    # Affichage de l'indicateur (Support Twitter Premium)
                    if chars > 25000:
                         st.error(f"⚠️ **Trop long !** {chars}/25000 caractères")
                    else:
                         st.caption(f"✅ {chars}/25000 caractères (Premium)")

                    new_content = st.text_area(
                        "Éditer le tweet", 
                        value=tweet['content'], 
                        key=f"edit_{tweet['id']}",
                        height=150 # Plus compact pour éviter les bugs visuels
                    )

                    # Boutons d'action
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        if st.button("✅ Valider & Planifier", key=f"approve_{tweet['id']}", type="primary"):
                            # Sauvegarder les modifications
                            if new_content != tweet['content']:
                                update_tweet_content(tweet['id'], new_content)
                            
                            if new_img_url != tweet.get('image_url', ''):
                                update_tweet_image(tweet['id'], new_img_url)
                            
                            approve_tweet(tweet['id'])
                            st.success("Tweet validé et ajouté à la file d'attente !")
                            st.rerun()
                with col2:
                    if st.button("❌ Rejeter", key=f"reject_{tweet['id']}"):
                        reject_tweet(tweet['id'])
                        st.warning("Tweet rejeté")
                        st.rerun()

# --- TOP TWEETS ---
elif page == "🏆 Top Tweets":
    st.header("🏆 Top Tweets Français Tech")
    
    st.info("📊 Récupère les 3 tweets français les plus populaires des dernières 24h sur l'IA, Twitch, Crypto et Jeux Vidéo")
    
    from tools.twitter_scraper import scrape_top_french_tech_tweets
    
    # Avertissement
    st.success("✅ Utilise le scraping web (pas de quota API)")
    st.caption("⏱️ Le chargement peut prendre 10-20 secondes...")
    
    if st.button("🔄 Actualiser le Top 3", type="primary"):
        with st.spinner("Scraping Twitter..."):
            try:
                # Utiliser asyncio pour appeler la fonction asynchrone
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                top_tweets = loop.run_until_complete(scrape_top_french_tech_tweets())
                loop.close()
                
                st.session_state['top_tweets'] = top_tweets
                st.session_state['last_refresh'] = datetime.now()
                
                if not top_tweets:
                    st.warning("⚠️ Aucun tweet trouvé. Vérifiez les logs du terminal pour plus de détails.")
            except Exception as e:
                st.error(f"❌ Erreur lors du scraping : {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Affichage des résultats
    if 'top_tweets' in st.session_state and st.session_state['top_tweets']:
        st.success(f"✅ Dernière mise à jour : {st.session_state.get('last_refresh', 'N/A').strftime('%Y-%m-%d %H:%M:%S')}")
        
        for i, tweet in enumerate(st.session_state['top_tweets'], 1):
            with st.container():
                st.markdown("---")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### #{i} - {tweet['text'][:100]}...")
                    st.caption(f"🕒 {tweet['created_at'].strftime('%Y-%m-%d %H:%M')} | 🏷️ {tweet.get('topic', 'N/A')}")
                    st.markdown(f"[🔗 Voir le tweet]({tweet['url']})")
                
                with col2:
                    st.metric("❤️ Likes", f"{tweet['likes']:,}")
                    st.metric("🔄 Retweets", f"{tweet['retweets']:,}")
                    st.metric("� Vues", f"{tweet.get('views', 0):,}")
                    st.metric("�📊 Score", f"{tweet['score']:,}")
    
    elif 'top_tweets' in st.session_state and not st.session_state['top_tweets']:
        st.warning("Aucun tweet trouvé pour les critères sélectionnés.")
    else:
        st.info("👆 Cliquez sur 'Actualiser' pour récupérer les meilleurs tweets !")

# --- QUEUE ---
elif page == "File d'attente":
    st.header("📋 File d'attente")
    
    from database import send_tweet_now
    
    pending_tweets = get_all_pending_tweets()
    
    if not pending_tweets:
        st.info("Aucun tweet en attente.")
    else:
        st.write(f"**{len(pending_tweets)} tweet(s) en attente**")
        
        for tweet in pending_tweets:
            with st.expander(f"📅 {tweet['scheduled_time']} - {tweet['content'][:50]}..."):
                st.code(tweet['content'])
                st.write(f"**Heure programmée** : {tweet['scheduled_time']}")
                
                if tweet.get('source_url'):
                    st.write(f"**Source** : {tweet['source_url']}")
                if tweet.get('image_url'):
                    try:
                        st.image(tweet['image_url'], use_container_width=True)
                    except:
                        st.write(f"🖼️ Image : {tweet['image_url']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Envoyer maintenant", key=f"send_now_{tweet['id']}", type="primary"):
                        send_tweet_now(tweet['id'])
                        st.success("Tweet sera envoyé dans ~1 minute !")
                        st.rerun()
                with col2:
                    if st.button("🗑️ Supprimer", key=f"del_{tweet['id']}"):
                        delete_scheduled_tweet(tweet['id'])
                        st.rerun()

# --- ACTIVITY ---
elif page == "Activité de veille":
    st.header("📊 Activité de veille")
    
    # Récupérer tous les tweets (pending + sent) avec source_url
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tweets 
        WHERE source_url IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT 50
    ''')
    activities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not activities:
        st.info("Aucune activité de veille pour le moment. La veille génère des tweets automatiquement quand elle trouve du nouveau contenu.")
    else:
        st.write(f"**{len(activities)} contenus découverts**")
        
        for activity in activities:
            status_emoji = {
                'pending': '⏳',
                'sent': '✅',
                'failed': '❌',
                'skipped': '⏭️'
            }.get(activity['status'], '❓')
            
            with st.expander(f"{status_emoji} {activity['scheduled_time']} - {activity['content'][:60]}..."):
                st.write(f"**Statut** : {activity['status']}")
                st.write(f"**Source** : [{activity['source_url']}]({activity['source_url']})")
                
                # Afficher l'image si disponible
                if activity.get('image_url'):
                    try:
                        st.image(activity['image_url'], caption="Image de l'article", use_container_width=True)
                    except:
                        st.write(f"Image : {activity['image_url']}")
                
                st.write(f"**Tweet** :")
                st.code(activity['content'])
                if activity['error_message']:
                    st.error(f"Erreur : {activity['error_message']}")

# --- MONITORING ---
elif page == "Veille Automatique":
    st.header("📡 Veille Automatique")
    
    with st.form("add_topic"):
        col1, col2 = st.columns([2, 1])
        with col1:
            new_topic = st.text_input("Sujet, Mot-clé ou URL")
        with col2:
            source_type = st.selectbox("Type de source", ["web_search", "twitter", "specific_url"])
            
        interval = st.number_input("Intervalle (minutes)", min_value=10, value=60)
        
        if st.form_submit_button("Ajouter"):
            add_monitored_topic(new_topic, interval, source_type)
            st.success(f"Sujet '{new_topic}' ({source_type}) ajouté !")
            st.success(f"Sujet '{new_topic}' ({source_type}) ajouté !")
            st.success(f"Sujet '{new_topic}' ({source_type}) ajouté !")
            st.rerun()
            
    st.markdown("---")
    
    # Zone de Debug / Reload
    with st.expander("🔧 Debug / Persistance"):
        import os
        st.write(f"**FIXED_TOPICS Env Var**: `{os.getenv('FIXED_TOPICS', 'Not Set')}`")
        if st.button("🔄 Recharger les sujets fixes (Env)"):
            msg = load_fixed_topics()
            st.info(msg)
            st.rerun()
            
    if st.button("🔄 Lancer la veille maintenant (Force Run)", type="primary"):
        with st.spinner("Exécution du cycle de veille en cours... (Cela peut prendre quelques minutes)"):
            try:
                # On lance le cycle de manière synchrone pour l'interface
                run_monitoring_cycle()
                st.success("Cycle de veille terminé ! Vérifiez l'onglet 'Validation' ou 'Activité'.")
            except Exception as e:
                st.error(f"Erreur lors de l'exécution : {str(e)}")
            
    st.subheader("Sujets actifs")
    topics = get_active_topics()
    
    if not topics:
        st.info("Aucun sujet surveillé.")
    else:
        for t in topics:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"**{t['query']}**")
            col2.write(f"Type: `{t.get('source_type', 'web_search')}`")
            col3.write(f"Toutes les {t['interval_minutes']} min")
            if col4.button("🗑️", key=f"del_topic_{t['id']}"):
                delete_monitored_topic(t['id'])
                st.rerun()

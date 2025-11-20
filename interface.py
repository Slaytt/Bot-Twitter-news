import streamlit as st
import asyncio
from datetime import datetime, timedelta
from tools.scraper import scrape_website
from tools.content_generator import generate_tweet_content
import database
from database import (
    init_db, get_monthly_count, add_scheduled_tweet, get_all_pending_tweets, 
    delete_scheduled_tweet, get_active_topics, add_monitored_topic, 
    delete_monitored_topic
)

# Ensure DB is initialized
init_db()

st.set_page_config(page_title="Twitter Bot Manager", page_icon="🤖", layout="wide")

st.title("🤖 Twitter Bot Manager")

# Sidebar Navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Générateur de Tweets", "✅ Validation", "File d'attente", "Activité de veille", "Veille Automatique"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.header("Tableau de bord")
    
    col1, col2 = st.columns(2)
    
    with col1:
        count = get_monthly_count()
        limit = 500
        st.metric("Tweets envoyés ce mois", f"{count} / {limit}", delta=limit-count, delta_color="normal")
        st.progress(count / limit)
        
    with col2:
        pending = len(get_all_pending_tweets())
        st.metric("Tweets en attente", pending)

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
        st.caption(f"Caractères: {len(edited_tweet)} / 280")
        
        if len(edited_tweet) > 280:
            st.warning("Attention : Le tweet dépasse 280 caractères !")
            
        col1, col2 = st.columns(2)
        with col1:
            schedule_date = st.date_input("Date d'envoi", value=datetime.now())
        with col2:
            schedule_time = st.time_input("Heure d'envoi", value=datetime.now())
        
        if st.button("Planifier l'envoi", type="primary"):
            run_at = datetime.combine(schedule_date, schedule_time)
            add_scheduled_tweet(edited_tweet, run_at)
            st.success(f"Tweet planifié pour le {run_at} !")
            st.session_state.tweet_preview = None
            st.rerun()

# --- VALIDATION ---
elif page == "✅ Validation":
    st.header("✅ Validation des Tweets")
    
    from database import get_tweets_awaiting_approval, approve_tweet, reject_tweet, update_tweet_content
    
    awaiting = get_tweets_awaiting_approval()
    
    if not awaiting:
        st.success("🎉 Aucun tweet en attente de validation !")
    else:
        st.write(f"**{len(awaiting)} tweet(s) en attente de validation**")
        
        for tweet in awaiting:
            with st.container():
                st.markdown("---")
                
                col_img, col_content = st.columns([1, 2])
                
                # Colonne Image
                with col_img:
                    if tweet.get('image_url'):
                        try:
                            st.image(tweet['image_url'], use_container_width=True)
                        except:
                            st.write(f"🖼️ Image: {tweet['image_url'][:50]}...")
                    else:
                        st.info("Pas d'image")
                        
                # Colonne Contenu (Éditable)
                with col_content:
                    st.caption(f"📅 Programmé pour : {tweet['scheduled_time']}")
                    if tweet.get('source_url'):
                        st.caption(f"🔗 Source : {tweet['source_url']}")
                        
                    # Zone d'édition
                    new_content = st.text_area(
                        "Éditer le tweet", 
                        value=tweet['content'], 
                        key=f"edit_{tweet['id']}",
                        height=200
                    )
                    
                    # Compteur de caractères
                    chars = len(new_content)
                    if chars > 280:
                        st.warning(f"⚠️ {chars}/280 caractères (Trop long !)")
                    else:
                        st.caption(f"✅ {chars}/280 caractères")
                
                # Boutons d'action
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("✅ Valider & Envoyer", key=f"approve_{tweet['id']}", type="primary"):
                        # Sauvegarder les modifications d'abord
                        if new_content != tweet['content']:
                            update_tweet_content(tweet['id'], new_content)
                        
                        approve_tweet(tweet['id'])
                        st.success("Tweet mis à jour et approuvé !")
                        st.rerun()
                with col2:
                    if st.button("❌ Rejeter", key=f"reject_{tweet['id']}"):
                        reject_tweet(tweet['id'])
                        st.warning("Tweet rejeté")
                        st.rerun()

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
            st.rerun()
            
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

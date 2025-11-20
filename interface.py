import streamlit as st
import asyncio
from datetime import datetime, timedelta
from tools.scraper import scrape_website
from tools.content_generator import generate_tweet_content
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
page = st.sidebar.radio("Navigation", ["Dashboard", "Générateur de Tweets", "File d'attente", "Veille Automatique"])

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
            del st.session_state['generated_tweet']
            st.rerun()

# --- QUEUE ---
elif page == "File d'attente":
    st.header("⏳ File d'attente")
    
    tweets = get_all_pending_tweets()
    
    if not tweets:
        st.info("Aucun tweet en attente.")
    else:
        for tweet in tweets:
            with st.expander(f"{tweet['scheduled_time']} - {tweet['content'][:50]}..."):
                st.write(tweet['content'])
                if st.button("Supprimer", key=f"del_{tweet['id']}"):
                    delete_scheduled_tweet(tweet['id'])
                    st.rerun()

# --- MONITORING ---
elif page == "Veille Automatique":
    st.header("📡 Veille Automatique")
    
    with st.form("add_topic"):
        new_topic = st.text_input("Nouveau sujet à surveiller")
        interval = st.number_input("Intervalle (minutes)", min_value=10, value=60)
        if st.form_submit_button("Ajouter"):
            add_monitored_topic(new_topic, interval)
            st.success(f"Sujet '{new_topic}' ajouté !")
            st.rerun()
            
    st.subheader("Sujets actifs")
    topics = get_active_topics()
    
    if not topics:
        st.info("Aucun sujet surveillé.")
    else:
        for t in topics:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{t['query']}**")
            col2.write(f"Toutes les {t['interval_minutes']} min")
            if col3.button("🗑️", key=f"del_topic_{t['id']}"):
                delete_monitored_topic(t['id'])
                st.rerun()

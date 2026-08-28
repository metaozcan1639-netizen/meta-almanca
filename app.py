import streamlit as st
from openai import OpenAI
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca B2 Yolculuğu",
    page_icon="🇩🇪",
    layout="wide"
)

# --- API Anahtarı ve Model Başlatma ---
# API Key'i Render Environment Variable'dan veya kullanıcı girdisinden alacağız
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.sidebar.warning("⚠️ API Anahtarı girilmedi. Sol menüden giriniz.")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")

client = OpenAI(api_key=api_key) if api_key else None

# --- Yan Menü (Sidebar) & İstatistikler ---
st.sidebar.title("📊 İlerleme Paneli")
st.sidebar.markdown("---")
st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")
st.sidebar.metric(label="Öğrenilen Kelime", value="142 / 3000")

# B2 Hedef İlerleme Çubuğu
progress = 142 / 3000
st.sidebar.write("**B2 Hedef Yüzdesi:**")
st.sidebar.progress(progress)

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 7/24 Almanca B2 Öğrenme Asistanı")
st.caption("Arayüz üzerinden pratik yapın, hatalarınızı anında düzeltin.")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["💬 AI Öğretmen ile Sohbet", "📚 Kelime Laboratuvarı (SRS)", "🎯 Günlük Görevler"])

# --- TAB 1: AI Sohbet ve Düzeltme Ekranı ---
with tab1:
    st.subheader("Almanca Pratik ve Anında Gramer Düzeltme")
    
    # Sohbet Geçmişi Hafızası
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "Sen Almanca öğretmenisin. Kullanıcının seviyesi B1-B2 yolunda. Yanıtlarını Almanca ver. Kullanıcı gramer veya kelime hatası yaparsa, yanıtının en başında hatayı düzelt (Örn: '❌ Hata: ich bin gegangen | ✅ Doğru: Ich bin gegangen') ve ardından sohbeti devam ettir."}
        ]

    # Eski Mesajları Ekrana Yazdır
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Kullanıcı Mesaj Girişi
    if prompt := st.chat_input("Almanca bir şeyler yazın... (Örn: Heute habe ich viel gearbeitet.)"):
        if not client:
            st.error("Lütfen önce API Anahtarınızı sol menüden girin!")
        else:
            # Kullanıcı mesajını ekle
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # AI Yanıtı Oluştur
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                # OpenAI API Çağrısı
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo", # Veya gpt-4o / groq / gemini
                    messages=st.session_state.messages,
                    stream=True,
                )
                
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- TAB 2: Kelime Laboratuvarı ---
with tab2:
    st.subheader("Aralıklı Tekrar Sistemi (SRS)")
    st.write("Bugün tekrar etmeniz gereken kelimeler:")
    
    # Örnek Kelime Veri Tablosu
    words_data = [
        {"Kelime": "die Entscheidung", "Anlamı": "Karar", "Seviye": "B1", "Durum": "Bugün Tekrar Et"},
        {"Kelime": "verantwortlich", "Anlamı": "Sorumlu", "Seviye": "B2", "Durum": "3 Gün Sonra"},
        {"Kelime": "beeinflussen", "Anlamı": "Etkilemek", "Seviye": "B2", "Durum": "Öğrenildi"},
    ]
    st.table(words_data)

# --- TAB 3: Günlük Görevler ---
with tab3:
    st.subheader("Bugünün B2 Hedefleri")
    st.checkbox("10 yeni B2 seviye kelime ezberle", value=True)
    st.checkbox("AI Öğretmen ile en az 5 dakika yazılı sohbet et", value=False)
    st.checkbox("1 adet B2 Paragraf Okuması yap", value=False)
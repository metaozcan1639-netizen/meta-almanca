import streamlit as st
from groq import Groq
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca B2 Yolculuğu",
    page_icon="🇩🇪",
    layout="wide"
)

# --- API Anahtarı ve Model Başlatma ---
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.sidebar.warning("⚠️ Groq API Anahtarı girilmedi. Lütfen menüden giriniz.")
    api_key = st.sidebar.text_input("Groq API Key (gsk_ ile başlar)", type="password")

client = Groq(api_key=api_key) if api_key else None

# --- Yan Menü (Sidebar) & İstatistikler ---
st.sidebar.title("📊 İlerleme Paneli")
st.sidebar.markdown("---")
st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")
st.sidebar.metric(label="Öğrenilen Kelime", value="142 / 3000")

progress = 142 / 3000
st.sidebar.write("**B2 Hedef Yüzdesi:**")
st.sidebar.progress(progress)

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 7/24 Almanca B2 Öğrenme Asistanı")
st.caption("Arayüz üzerinden pratik yapın, hatalarınızı anında düzeltin. (Altyapı: Groq Llama 3)")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["💬 AI Öğretmen ile Sohbet", "📚 Kelime Laboratuvarı (SRS)", "🎯 Günlük Görevler"])

# --- TAB 1: AI Sohbet ve Düzeltme Ekranı ---
with tab1:
    st.subheader("Almanca Pratik ve Anında Gramer Düzeltme")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "Sen Alman bir öğretmensin. Öğrencin B1-B2 seviyesine ulaşmaya çalışıyor. Bütün cevaplarını tamamen Almanca olarak vermelisin. Eğer kullanıcı Almanca gramer, cümle yapısı veya kelime hatası yaparsa, yanıtına muhakkak hatayı düzelterek başla. (Örnek format: '❌ Hata: [kullanıcının yazdığı] | ✅ Doğru: [doğru hali]'). Düzeltmeyi yaptıktan sonra sohbete devam et."}
        ]

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if prompt := st.chat_input("Almanca bir yazı yazın... (Örn: Heute habe ich viel gearbeitet.)"):
        if not client:
            st.error("Lütfen önce Groq API Anahtarınızı sol menüden girin!")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    response = client.chat.completions.create(
                        messages=st.session_state.messages,
                        model="llama3-8b", 
                        stream=True,
                    )
                    
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")

# --- TAB 2: Kelime Laboratuvarı ---
with tab2:
    st.subheader("Aralıklı Tekrar Sistemi (SRS)")
    st.write("Bugün tekrar etmeniz gereken kelimeler:")
    
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

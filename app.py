import streamlit as st
from groq import Groq
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca Rehberli Öğrenme & Test Sistemi",
    page_icon="🇩🇪",
    layout="wide"
)

# --- API Anahtarı ve Model Başlatma ---
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.sidebar.warning("⚠️ Groq API Anahtarı girilmedi. Lütfen menüden giriniz.")
    api_key = st.sidebar.text_input("Groq API Key (gsk_ ile başlar)", type="password")

client = Groq(api_key=api_key) if api_key else None

# --- Yan Menü (Sidebar) & Kur İlerleme Paneli ---
st.sidebar.title("📊 Kur ve İlerleme Paneli")
st.sidebar.markdown("---")

current_level = st.sidebar.selectbox("Öğrenmek İstediğin Kur/Seviye", ["A1 Kurulum", "A2 Temel", "B1 Orta", "B2 İleri (Hedef)", "C1 Uzman", "C2 Anadil"])

st.sidebar.info("💡 **Önce Öğren, Sonra Test Ol:** Sistem her konuyu detaylıca Türkçe anlatır, ardından seni test eder.")
st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")
st.sidebar.metric(label="Öğrenilen Kelime", value="142 / 3000")

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 Adım Adım Almanca: Önce Ders, Sonra Sınav")
st.caption(f"Aktif Seviye: {current_level} | Konular sindirilerek ve test edilerek işlenir.")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["📖 Ders ve Sınav Odası", "📚 Kelime Laboratuvarı (SRS)", "🎯 Kur Görevleri"])

# --- TAB 1: AI Sohbet ve Öğret-Test Sistemi ---
with tab1:
    st.subheader("Birebir Özel Almanca Eğitmeni")
    
    # Yeni Öğret-Test Sistem Promptu
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    "Sen çok titiz ve disiplinli bir Almanca öğretmenisin. Öğrencin Almanca'yı hiç bilmiyor "
                    "ve konuları adım adım, sindirerek öğrenmek istiyor. Kesinlikle şu kurala uymalısın:\n\n"
                    "1. **Önce Ders (Anlatım):** Öğrenci bir konu istediğinde veya soru sorduğunda, konuyu en temelden Türkçe olarak, bol örnekle ve anlaşılır şekilde detaylıca anlat.\n"
                    "2. **Sonra Test (Sınav):** Konu anlatımı biter bitmez, öğrencinin öğrendiklerini pekiştirmesi için hemen oracıkta 1 veya 2 adet mini test sorusu (çeviri görevi veya boşluk doldurma) sor ve öğrencinin cevap vermesini bekle.\n"
                    "3. **Değerlendirme:** Öğrenci test sorusunu yanıtladığında cevabını Türkçe olarak değerlendir, doğruysa tebrik et, yanlışsa düzelt ve bir sonraki konuya ya da teste geç.\n\n"
                    "Şu an ilk açılış için öğrenciye hangi seviyeden (örneğin A1 alfabe, artikeller veya günlük selamlaşma ile mi) başlamak istediğini sor ve kısa bir giriş yap."
                )
            }
        ]

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if prompt := st.chat_input("Örn: 'Bana A1 seviyesinden bugünkü dersi başlat ve anlat.' yazabilirsiniz."):
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
                        model="openai/gpt-oss-120b",
                        stream=True,
                    )
                    
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                except Exception as e:
                    st.error(f"API Bağlantı Hatası: {e}")

# --- TAB 2: Kelime Laboratuvarı ---
with tab2:
    st.subheader("Aralıklı Tekrar Sistemi (SRS)")
    st.write("Bu kurda ezberlemen gereken temel kelimeler:")
    
    words_data = [
        {"Kelime": "der Tisch", "Anlamı": "Masa", "Seviye": "A1", "Durum": "Öğreniliyor"},
        {"Kelime": "das Haus", "Anlamı": "Ev", "Seviye": "A1", "Durum": "Yeni"},
    ]
    st.table(words_data)

# --- TAB 3: Günlük Görevler ---
with tab3:
    st.subheader("Ders ve Sınav Görevleri")
    st.checkbox("Bugünkü ders anlatımını dikkatle oku ve not al", value=False)
    st.checkbox("Öğretmenin sorduğu mini test sorularını eksiksiz yanıtla", value=False)

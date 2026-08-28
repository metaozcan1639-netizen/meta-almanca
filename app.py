import streamlit as st
from groq import Groq
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca Görsel & Interaktif Akademi",
    page_icon="🇩🇪",
    layout="wide"
)

# --- Özel CSS ile Görsel Kart Tasarımları ---
st.markdown("""
<style>
    .info-card {
        background-color: #1e293b;
        border-left: 5px solid #3b82f6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .rule-box {
        background-color: #0f172a;
        border: 1px solid #334155;
        padding: 15px;
        border-radius: 8px;
        color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# --- API Anahtarı ve Model Başlatma ---
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.sidebar.warning("⚠️ Groq API Anahtarı girilmedi. Lütfen menüden giriniz.")
    api_key = st.sidebar.text_input("Groq API Key (gsk_ ile başlar)", type="password")

client = Groq(api_key=api_key) if api_key else None

# --- Yan Menü (Sidebar) & Müfredat Paneli ---
st.sidebar.title("🗺️ Müfredat ve İlerleme")
st.sidebar.markdown("---")

current_level = st.sidebar.selectbox("Aktif Kur / Seviye", ["A1 - Temel Yapılar", "A2 - Günlük Hayat", "B1 - Olaylar & Fikirler", "B2 - Profesyonel Akıcılık", "C1/C2 - Uzmanlık"])

st.sidebar.markdown("""
<div class="rule-box">
<b>🎯 Akademi Disiplini:</b><br>
• Görsel Kartlar & Tablolar<br>
• Sokratik Mantık Yürütme<br>
• Gerçek Hayat Senaryoları
</div>
""", unsafe_allow_html=True)

st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")
st.sidebar.metric(label="Tamamlanan Senaryo", value="12 / 150")

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 İnteraktif & Görsel Almanca Akademisi")
st.caption(f"Aktif Modül: {current_level} | Düz yazı yok, mantık kurma ve senaryo temelli öğrenme var.")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["🏛️ Görsel Ders & Senaryo Odası", "📊 Kelime Haritası & SRS", "📋 Kur Sınavları"])

# --- TAB 1: Görsel Ders ve Senaryo Odası ---
with tab1:
    st.subheader("Görsel Anlatımlı Özel Eğitmen")
    
    # Gelişmiş Eğitim ve Görsel Sistem Promptu
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    "Sen çok yenilikçi, görsel hafızayı kullanan ve senaryo tabanlı öğreten üst düzey bir Almanca koçusun. "
                    "Öğrenci düz yazılardan ve sıkıcı testlerden sıkılıyor. Bu yüzden kuralları anlatırken kesinlikle şunları yap:\n\n"
                    "1. **Görsel Tablolar ve Bloklar:** Konuyu anlatırken Markdown tabloları, emoji kartları ve görsel şemalar kullan. Asla düz uzun paragraf yazma.\n"
                    "2. **Mantık Kodlaması:** Kelimenin veya gramerin neden öyle olduğunu mantıksal bir hikaye veya görsel benzetmeyle açıkla (Türkçe olarak).\n"
                    "3. **Gerçek Hayat Senaryosu:** Sadece kural anlatıp bırakma; hemen ardından 'Şu an Berlin'desin ve trende bilet kontrolü yapılıyor, memura şu cümleyi kurman lazım' gibi interaktif bir senaryo görevi ver.\n\n"
                    "İlk mesajda öğrenciye hangi senaryo dünyasından (günlük yaşam, iş hayatı veya seyahat) başlamak istediğini sorarak harika bir görsel karşılama yap."
                )
            }
        ]

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if prompt := st.chat_input("Örn: 'Bana Akkusativ ve Dativ arasındaki farkı görsel tablolarla ve senaryoyla anlat.' yazabilirsin."):
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

# --- TAB 2: Kelime Haritası ---
with tab2:
    st.subheader("Görsel Kelime Ağacı ve SRS")
    st.write("Bağlam ve kategorilere göre ayrılmış aktif kelime havuzunuz:")
    
    vocab_data = [
        {"Kategori": "Seyahat & Ulaşım", "Almanca": "der Fahrplan", "Türkçe": "Tarife / Sefer Saatleri", "Durum": "Aktif Öğreniliyor"},
        {"Kategori": "İş & Kurumsal", "Almanca": "die Besprechung", "Türkçe": "Toplantı", "Durum": "Tekrar Edilecek"},
        {"Kategori": "Günlük Yaşam", "Anlamı": "die Kaffeepause", "Türkçe": "Kahve Molası", "Durum": "Pekiştirildi"}
    ]
    st.table(vocab_data)

# --- TAB 3: Kur Sınavları ---
with tab3:
    st.subheader("Senaryo Bazlı Değerlendirme Sınavları")
    st.info("Bu modülde çoktan seçmeli ezberler yerine tamamen kurgusal senaryo başarı testleri yer alır.")
    st.checkbox("Senaryo 1: Restoranda yanlış gelen yemeği kibarca değiştirme görevi", value=False)
    st.checkbox("Senaryo 2: Otelde oda arızası için resepsiyona şikayet maili yazma", value=False)

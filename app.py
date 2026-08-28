import streamlit as st
from groq import Groq
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca Görsel & Interaktif Akademi",
    page_icon="🇩🇪",
    layout="wide"
)

# --- Özel CSS (Arayüz ve Sohbet Kutusu Ayarları) ---
st.markdown("""
<style>
    /* Kur kutusu stili */
    .rule-box {
        background-color: #0f172a;
        border: 1px solid #334155;
        padding: 12px;
        border-radius: 8px;
        color: #f8fafc;
        font-size: 14px;
    }
    
    /* Sohbet Girdi Kutusunu Sağ Alta Daraltıp Sabitleme */
    [data-testid="stChatInput"] {
        max-width: 600px !important; 
        margin-left: auto !important; 
        margin-right: 20px !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- API Anahtarı ve Model Başlatma ---
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.sidebar.warning("⚠️ Groq API Anahtarı girilmedi.")
    api_key = st.sidebar.text_input("Groq API Key (gsk_ ile başlar)", type="password")

client = Groq(api_key=api_key) if api_key else None

# --- Yan Menü (Sidebar) ---
st.sidebar.title("🗺️ Müfredat ve Yol Haritası")
st.sidebar.markdown("---")

selected_level = st.sidebar.selectbox(
    "Önce Kur Seçin:", 
    ["A1 - Temel Yapılar (Sıfırdan)", "A2 - Günlük Yaşam", "B1 - Olaylar & Fikirler", "B2 - Profesyonel Akıcılık"]
)

if st.sidebar.button("🔄 Sohbeti ve Dersi Sıfırla"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown(f"""
<div class="rule-box">
<b>📌 Seçilen Kur:</b> {selected_level}<br><br>
<b>Eğitim Modeli:</b> Mikro-Öğrenme. Sadece 1 kalıp öğretilir, karakterlerle canlandırılır ve test edilir.
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 İnteraktif & Görsel Almanca Akademisi")
st.caption(f"Aktif Modül: {selected_level} | Bilgi bombardımanı yok, adım adım görsel canlandırma var.")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2 = st.tabs(["🏛️ Canlandırmalı Ders Odası", "📋 Kur Sınavları"])

with tab1:
    
    # 📌 MİKRO-ÖĞRENME VE GÖRSEL CANLANDIRMA PROMPTU
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    f"Sen çok disiplinli, 'Mikro-Öğrenme' (Micro-learning) metodunu uygulayan bir Almanca öğretmenisin. "
                    f"Öğrenci şu an '{selected_level}' kurunda.\n\n"
                    "ŞU KATI KURALLARA KESİNLİKLE UYACAKSIN:\n"
                    "1. BİLGİ BOMBARDIMANI YASAK: Asla uzun listeler veya tablolar verme! Her seferinde SADECE BİR veya İKİ kelime/kalıp öğret. "
                    "(Örn: Bir derste sadece 'Adın ne?' sorusu ve cevabı işlenir).\n"
                    "2. GÖRSEL DİYALOG (CANLANDIRMA): Öğrettiğin o tek kalıbı, EKRANDA İKİ KİŞİ KONUŞUYORMUŞ GİBİ emojilerle canlandır. "
                    "(Örn: 🧑🏻 Ali: Hallo! Wie heißt du? | 👩🏼 Anna: Ich heiße Anna.). Başka hiçbir gereksiz detay verme.\n"
                    "3. MİKRO TEST: Diyaloğu verdikten hemen sonra öğrenciye tek bir pratik sorusu sor (Örn: 'Şimdi sen adını söyle').\n"
                    "4. ONAY KİLİDİ: Öğrenci o mini-testi doğru yapmadan asla yeni bir kalıba veya senaryoya geçme! Yanlış yaparsa düzeltip tekrar sor."
                )
            }
        ]

    # Mesajları Ekrana Yazdırma Alanı
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

# --- Mesaj Yazma Alanı (Özel CSS ile Sağ Alta Sabitlendi) ---
if prompt := st.chat_input("Mesajınızı buraya yazın (Örn: 'Hazırım, ilk dersi canlandıralım')..."):
    if not client:
        st.error("Lütfen önce sol menüden Groq API Anahtarınızı girin!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with tab1:
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

# --- Diğer Sekmeler ---
with tab2:
    st.subheader("Kur Atlama Değerlendirmeleri")
    st.info("Canlandırmalı dersleri tamamladığınızda buradaki pratik senaryo sınavları aktifleşecektir.")

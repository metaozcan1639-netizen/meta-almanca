import streamlit as st
from groq import Groq
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca A1-C2 Dil Koçu",
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

# Seviye Seçimi (A1'den C2'ye)
current_level = st.sidebar.selectbox("Mevcut Hedef / Kur Seç", ["A1 Kurulum", "A2 Temel", "B1 Orta", "B2 İleri (Hedef)", "C1 Uzman", "C2 Anadil"])

# Kur İlerleme Durumu
if current_level == "A1 Kurulum":
    progress_val = 0.15
    st.sidebar.info("A1 Seviyesi: Temel tanışma, günlük ifadeler.")
elif current_level == "A2 Temel":
    progress_val = 0.35
    st.sidebar.info("A2 Seviyesi: Basit cümleler, yakın geçmiş.")
elif current_level == "B1 Orta":
    progress_val = 0.60
    st.sidebar.info("B1 Seviyesi: Olayları anlatma, fikir belirtme.")
elif current_level == "B2 İleri (Hedef)":
    progress_val = 0.85
    st.sidebar.info("B2 Seviyesi: Akıcı diyalog, karmaşık metinler.")
elif current_level == "C1 Uzman":
    progress_val = 0.95
    st.sidebar.info("C1 Seviyesi: Akademik ve profesyonel yetkinlik.")
else:
    progress_val = 1.0
    st.sidebar.info("C2 Seviyesi: Kusursuz hakimiyet.")

st.sidebar.write(f"**Kur İlerleme Durumu:**")
st.sidebar.progress(progress_val)
st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")
st.sidebar.metric(label="Öğrenilen Kelime", value="142 / 3000")

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 Akıllı Almanca Dil Koçu (A1 ➔ C2)")
st.caption("Açıklamaları Türkçe, pratikleri Almanca olan size özel kademeli koçluk sistemi.")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["💬 Rehberli AI Eğitmen", "📚 Kelime Laboratuvarı (SRS)", "🎯 Kur Görevleri"])

# --- TAB 1: AI Sohbet ve Türkçe Açıklamalı Düzeltme ---
with tab1:
    st.subheader("Aktif Pratik ve Anlaşılır Hata Düzeltme")
    
    # Yeni ve Türkçe açıklamalı sistem promptu
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    "Sen çok sabırlı, samimi ve profesyonel bir Almanca dil eğitmenisin. "
                    "Öğrencin Almanca'yı yeni öğreniyor ve açıklamaları kesinlikle TÜRKÇE istiyor. "
                    "Öğrenci sana Almanca bir cümle yazdığında şu formata kesinlikle uy:\n"
                    "1. ❌ **Hatalı Cümle:** Kullanıcının yazdığı.\n"
                    "2. ✅ **Doğru Cihaz/Cümle:** Doğru Almanca hali.\n"
                    "3. 💡 **Türkçe Açıklama:** Bu kuralın neden böyle olduğunu, kelime dizilimini veya grameri TÜRKÇE olarak çok net ve basit bir dille açıkla.\n"
                    "4. 🎯 **Sıradaki Görev:** Öğrencinin bu kuralı pekiştirmesi için Türkçe yönlendirmeyle mini bir pratik cümlesi kurmasını iste."
                )
            }
        ]

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if prompt := st.chat_input("Almanca bir cümle yazın veya Türkçe sorun... (Örn: Ich habe gestern arbeiten.)"):
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
    st.write("Seçtiğiniz kura ait tekrar etmeniz gereken kelimeler:")
    
    words_data = [
        {"Kelime": "die Arbeit", "Anlamı": "İş", "Seviye": "A1", "Durum": "Öğrenildi"},
        {"Kelime": "entscheiden", "Anlamı": "Karar vermek", "Seviye": "B1", "Durum": "Bugün Tekrar Et"},
        {"Kelime": "die Maßnahme", "Anlamı": "Önlem / Tedbir", "Seviye": "B2", "Durum": "Yeni"},
    ]
    st.table(words_data)

# --- TAB 3: Günlük Görevler ---
with tab3:
    st.subheader("Kur Atlama Görevleri")
    st.checkbox("Seçilen kur seviyesine uygun 10 temel kelimeyi ezberle", value=True)
    st.checkbox("Eğitmene Türkçe açıklamalı en az 3 farklı cümle gönder", value=False)
    st.checkbox("Geçmiş zaman (Präteritum / Perfekt) kurallarını tekrar et", value=False)

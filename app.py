import streamlit as st
from groq import Groq
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca Görsel & Interaktif Akademi",
    page_icon="🇩🇪",
    layout="wide"
)

# --- Özel CSS ---
st.markdown("""
<style>
    .rule-box {
        background-color: #0f172a;
        border: 1px solid #334155;
        padding: 12px;
        border-radius: 8px;
        color: #f8fafc;
        font-size: 14px;
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
    ["A1 - Temel Yapılar (Sıfırdan)", "A2 - Günlük Yaşam", "B1 - Olaylar & Fikirler", "B2 - Profesyonel Akıcılık", "C1/C2 - Uzmanlık"]
)

if st.sidebar.button("🔄 Sohbeti ve Dersi Sıfırla"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown(f"""
<div class="rule-box">
<b>📌 Seçilen Kur:</b> {selected_level}<br><br>
<b>Eğitim Modeli:</b> Onaylı İlerleme. Bir konuyu öğrenip testini geçmeden asla bir sonraki adıma geçilmez.
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 İnteraktif & Görsel Almanca Akademisi")
st.caption(f"Aktif Modül: {selected_level} | Konuyu Anla ➔ Testi Çöz ➔ Onayı Al ➔ İlerle")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["🏛️ Ders ve Pratik Odası", "📊 Kelime Haritası", "📋 Kur Sınavları"])

with tab1:
    st.subheader(f"Disiplinli Eğitmen Odası")
    
    # 📌 KATI ONAY SİSTEMLİ PROMPT
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    f"Sen çok disiplinli, adım adım ilerleyen bir Almanca öğretmenisin. Öğrenci şu an '{selected_level}' kurunda.\n\n"
                    "ŞU 3 KURALA KESİNLİKLE UYACAKSIN:\n"
                    "1. KİLİT SİSTEMİ: Öğrenciye bir konuyu anlattıktan sonra MUTLAKA o konuyla ilgili bir pratik sorusu sor (Örn: 'Şimdi sen çevir: ...'). "
                    "Öğrenci bu soruya DOĞRU CEVAP vermeden asla bir sonraki konuya geçme!\n"
                    "2. ADIM ADIM: İlk mesajında sadece kurun yol haritasını ver ve 'Hazırsan 1. Adım olan ... ile başlayalım mı?' diye onayı iste.\n"
                    "3. ONAY MEKANİZMASI: Öğrenci testi doğru çözerse '✅ Harika, bu konuyu başarıyla öğrendin! Şimdi 2. Adıma geçiyoruz' diyerek ilerle. Yanlış çözerse konuyu farklı bir örnekle tekrar anlat ve yeni bir test sor."
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

# --- Mesaj Yazma Alanı (Tüm ekranın en altına, sağ panele sabitlenir) ---
if prompt := st.chat_input("Mesajınızı buraya yazın (Örn: 'Hazırım, ilk derse başlayalım')..."):
    if not client:
        st.error("Lütfen önce sol menüden Groq API Anahtarınızı girin!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Sadece Tab 1 aktifken mesajların akması için (Streamlit yapısı gereği)
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
    st.subheader("Görsel Kelime Ağacı")
    st.write(f"Seçilen kur ({selected_level}) kelimeleri:")
    st.info("Bu alan ileride veritabanına bağlanarak öğrendiğiniz kelimeleri otomatik tutacaktır.")

with tab3:
    st.subheader("Kur Atlama Değerlendirmeleri")
    st.info("Tüm temel modülleri tamamlayıp öğretmenden onay aldığınızda buradaki final sınavları açılacaktır.")

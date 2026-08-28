import streamlit as st
from groq import Groq
import os

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="Almanca Görsel & Interaktif Akademi",
    page_icon="🇩🇪",
    layout="wide"
)

# --- Özel CSS (Arayüzü Düzenleme ve Temizleme) ---
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

# --- Yan Menü (Sidebar) & Kur Seçim Paneli ---
st.sidebar.title("🗺️ Müfredat ve Yol Haritası")
st.sidebar.markdown("---")

selected_level = st.sidebar.selectbox(
    "Önce Kur Seçin:", 
    ["A1 - Temel Yapılar (Sıfırdan)", "A2 - Günlük Yaşam", "B1 - Olaylar & Fikirler", "B2 - Profesyonel Akıcılık", "C1/C2 - Uzmanlık"]
)

# Kur değiştiğinde veya sıfırlama istendiğinde hafızayı yenilemek için buton
if st.sidebar.button("🔄 Sohbeti ve Dersi Sıfırla"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown(f"""
<div class="rule-box">
<b>📌 Seçilen Kur:</b> {selected_level}<br><br>
<b>Strateji:</b> Önce bu kurda ne öğreneceğimizi planlıyoruz, temelden başlayıp adım adım ilerliyoruz.
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.metric(label="Günlük Seri (Streak)", value="5 Gün 🔥")
st.sidebar.metric(label="Tamamlanan Görev", value="12 / 150")

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 İnteraktif & Görsel Almanca Akademisi")
st.caption(f"Aktif Modül: {selected_level} | Temelden İlerleyen Yapılandırılmış Eğitim Sistemi")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["🏛️ Ders ve Pratik Odası", "📊 Kelime Haritası & SRS", "📋 Kur Sınavları"])

# --- TAB 1: Ders ve Pratik Odası ---
with tab1:
    st.subheader(f"Hedef Kur: {selected_level}")
    
    # Sohbet Geçmişi ve Kur Bazlı Sistem Komutu
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    f"Sen çok disiplinli, görsel hafızayı kullanan ve pedagojik yaklaşımı mükemmel olan bir Almanca öğretmenisin. "
                    f"Öğrenci şu an '{selected_level}' kurunu seçti.\n\n"
                    "KESİN KURALLARIN:\n"
                    "1. Asla direkt karmaşık konulara veya rastgele senaryolara atlama.\n"
                    "2. İlk mesajda, seçilen bu kurda (örneğin A1 ise sıfırdan harfler, artikeller, temel tanışma; B2 ise ileri düzey yapılar) "
                    "adım adım nasıl bir yol izleyeceğimizi Türkçe olarak özetle.\n"
                    "3. Öğrenciye bu kurun **ilk temel dersini** görsel tablolar eşliğinde başlatmak isteyip istemediğini sor ve onayını bekle."
                )
            }
        ]
        # İlk açılışta öğretmenin kur yol haritasını çizmesi için tetikleyici ekleyelim
        # (Streamlit ilk yüklemede system promptunu işler)

    # Sohbet kutusundaki mesajları ekrana yazdır (System hariç)
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Kullanıcı Girdi Alanı (Ekranın en altında temiz bir şekilde yer alır)
    if prompt := st.chat_input("Örn: 'Seçtiğim kurun yol haritasını çıkar ve ilk dersten başlayalım.' yazın..."):
        if not client:
            st.error("Lütfen önce sol menüden Groq API Anahtarınızı girin!")
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
    st.write(f"Seçilen kur ({selected_level}) için temel kelime havuzu:")
    
    vocab_data = [
        {"Seviye": "A1 Temel", "Almanca": "das Jahr", "Türkçe": "Yıl", "Durum": "Sıradaki Ders"},
        {"Seviye": "A1 Temel", "Almanca": "die Schule", "Türkçe": "Okul", "Durum": "Öğreniliyor"},
    ]
    st.table(vocab_data)

# --- TAB 3: Kur Sınavları ---
with tab3:
    st.subheader("Kur Atlama Değerlendirmeleri")
    st.info("Seçtiğiniz kurun tüm temel modülleri tamamlandığında buradaki pratik senaryo sınavları aktifleşecektir.")
    st.checkbox("Modül 1 Temel Kavrama Testi", value=False)

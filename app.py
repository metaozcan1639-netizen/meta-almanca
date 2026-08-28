import streamlit as st
from datetime import datetime
import sqlite3

# --- Sayfa Konfigürasyonu ---
st.set_page_config(page_title="Almanca Dil Akademisi", page_icon="🇩🇪", layout="wide")

# --- CSS Ayarları ---
st.markdown("""
<style>
    .metric-box { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .header-text { color: #f8fafc; font-size: 24px; font-weight: bold; margin-bottom: 5px; }
    .sub-text { color: #94a3b8; font-size: 14px; }
    .nav-header { font-size: 18px; font-weight: bold; color: #fbbf24; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 5px;}
</style>
""", unsafe_allow_html=True)

# --- Veritabanı ve Oturum Yönetimi (Özet) ---
if "xp" not in st.session_state:
    st.session_state.xp = 150
if "streak" not in st.session_state:
    st.session_state.streak = 5
if "seviye" not in st.session_state:
    st.session_state.seviye = "A1 - Temel Yapılar"

# --- Yan Menü (Navigasyon) ---
st.sidebar.markdown('<div class="nav-header">🌍 Akademi Menüsü</div>', unsafe_allow_html=True)
sayfa = st.sidebar.radio(
    "Gitmek istediğiniz bölümü seçin:",
    ["🏠 Ana Ekran (Dashboard)", 
     "📖 Okuma (Lesen)", 
     "🎧 Dinleme (Hören)", 
     "✍️ Yazma (Schreiben)", 
     "🗣️ Konuşma (Sprechen)", 
     "🗂️ Kelime Kartları"]
)

st.sidebar.markdown('<div class="nav-header">⚙️ Ayarlar</div>', unsafe_allow_html=True)
st.session_state.seviye = st.sidebar.selectbox("Aktif Kur:", ["A1 - Temel", "A2 - Başlangıç", "B1 - Orta", "B2 - İleri", "C1 - Uzman", "C2 - Anadil"])

st.sidebar.markdown("---")
st.sidebar.write(f"🔥 **Seri:** {st.session_state.streak} Gün")
st.sidebar.write(f"🌟 **XP:** {st.session_state.xp}")

# ==========================================
# SAYFA İÇERİKLERİ YÖNLENDİRMESİ
# ==========================================

if sayfa == "🏠 Ana Ekran (Dashboard)":
    st.title("🇩🇪 Akademi Yönetim Paneli")
    st.write("Sisteme hoş geldin! Bugün hangi becerini geliştirmek istersin?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="header-text">Mevcut Kur</div><div class="sub-text">{st.session_state.seviye}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="header-text">İlerleme</div><div class="sub-text">%15 (Sonraki kura 850 XP)</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="header-text">Bugünkü Görevler</div><div class="sub-text">0/3 Tamamlandı</div></div>', unsafe_allow_html=True)
        
    st.write("---")
    st.subheader("📍 Müfredat Ağacı (A1)")
    st.info("Çalışmak istediğin konuyu buradan seçip sol menüden ilgili beceri odasına gidebilirsin.")
    
    with st.expander("Modül 1: Tanışma ve Temel İfadeler", expanded=True):
        st.checkbox("Alfabe ve Telaffuz Kuralları", value=True)
        st.checkbox("Selamlaşma ve Kendini Tanıtma", value=False)
        st.checkbox("Sayılar, Günler ve Aylar", value=False)
        
    with st.expander("Modül 2: Temel Gramer (İsimler ve Artikeller)"):
        st.checkbox("Der, Die, Das Mantığı")
        st.checkbox("Çoğul Yapılar")

elif sayfa == "📖 Okuma (Lesen)":
    st.title("📖 Okuma Odası (Lesen)")
    st.caption("Seviyene uygun metinler ve anlama testleri.")
    st.info("Yapay zeka burada senin seviyene göre kısa bir metin üretecek. Altında da okuduğunu anlama soruları olacak.")
    # AI Okuma entegrasyonu buraya gelecek

elif sayfa == "🎧 Dinleme (Hören)":
    st.title("🎧 Dinleme Odası (Hören)")
    st.caption("Sadece ses ve boşluk doldurma görevleri.")
    st.info("Burada ekranda metin olmayacak. Sadece bir oynatıcı (Play butonu) olacak. Sesi dinleyip aşağıya duyduklarını yazacaksın.")
    # AI Dinleme entegrasyonu buraya gelecek

elif sayfa == "✍️ Yazma (Schreiben)":
    st.title("✍️ Yazma Odası (Schreiben)")
    st.caption("Serbest yazım ve akademik düzeltme.")
    st.info("Sana bir senaryo verilecek (Örn: 'Arkadaşına doğum günü için mail yaz'). Sen yazacaksın, AI hatalarını Dativ/Akkusativ kurallarına göre detaylı analiz edecek.")
    # AI Yazma entegrasyonu buraya gelecek

elif sayfa == "🗣️ Konuşma (Sprechen)":
    st.title("🗣️ Konuşma Odası (Sprechen)")
    st.caption("Gerçek hayat senaryoları ve interaktif sohbet.")
    st.info("Burada sohbet kutusu (chat) aktif olacak. Restoran, havalimanı gibi senaryolarda yapay zeka ile karşılıklı rol yaparak konuşacaksın.")
    # AI Konuşma entegrasyonu buraya gelecek

elif sayfa == "🗂️ Kelime Kartları":
    st.title("🗂️ Odaklanmış Kelime Çalışması")
    st.caption("Tüm dikkatini tek bir karta verdiğin özel öğrenme alanı.")
    
    # Yeni Tekli Odak Kart Tasarımı
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; color: #3b82f6;'>die Entschuldigung</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-style: italic; color: #94a3b8;'>Entschuldigung, wo ist der Bahnhof?</p>", unsafe_allow_html=True)
            st.write("---")
            if st.button("🔄 Çevir ve Kontrol Et", use_container_width=True):
                st.success("🇹🇷 **Özür dilerim / Afedersiniz**\n\n*Afedersiniz, tren istasyonu nerede?*")
                c1, c2 = st.columns(2)
                c1.button("🔴 Zordu (Tekrar Sor)", use_container_width=True)
                c2.button("🟢 Kolaydı (Öğrendim)", use_container_width=True)

import streamlit as st
from groq import Groq
import os
import sqlite3
from datetime import datetime, timedelta

# --- 1. VERİTABANI (DATABASE) KURULUMU VE FONKSİYONLAR ---
def init_db():
    conn = sqlite3.connect('dil_akademisi.db', check_same_thread=False)
    c = conn.cursor()
    # Kelime Havuzu Tablosu (SRS Algoritması İçin)
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            almanca TEXT,
            turkce TEXT,
            seviye TEXT,
            ease_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 1,
            next_review DATE
        )
    ''')
    # Kullanıcı İstatistikleri (Streak ve Puan Takibi)
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_login DATE,
            total_xp INTEGER DEFAULT 0
        )
    ''')
    # Eğer tablo boşsa örnek kelimeler ve varsayılan istatistik ekle
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        c.execute("INSERT INTO stats (id, streak, last_login, total_xp) VALUES (1, 1, ?, 0)", (bugun,))
        
    c.execute("SELECT COUNT(*) FROM vocabulary")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        ornek_kelimeler = [
            ("Hallo", "Merhaba", "A1", bugun),
            ("Danke", "Teşekkürler", "A1", bugun + timedelta(days=1)),
            ("das Auto", "Araba", "A1", bugun)
        ]
        c.executemany("INSERT INTO vocabulary (almanca, turkce, seviye, next_review) VALUES (?, ?, ?, ?)", ornek_kelimeler)
    
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- Günlük Giriş ve Streak Kontrolü ---
bugun = datetime.now().date()
c.execute("SELECT streak, last_login FROM stats WHERE id=1")
stat_row = c.fetchone()
current_streak, last_login_str = stat_row[0], stat_row[1]

# Eğer son giriş dünden önceyse seriyi sıfırla, bugün ilk defa giriyorsa seriyi 1 artır
if last_login_str:
    last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
    if last_login_date == bugun - timedelta(days=1):
        current_streak += 1
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE id=1", (current_streak, bugun))
        conn.commit()
    elif last_login_date < bugun - timedelta(days=1):
        current_streak = 1 # Seri bozuldu
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE id=1", (current_streak, bugun))
        conn.commit()

# --- Sayfa Konfigürasyonu ---
st.set_page_config(page_title="Almanca Görsel & Interaktif Akademi", page_icon="🇩🇪", layout="wide")

# --- Özel CSS ---
st.markdown("""
<style>
    .rule-box { background-color: #0f172a; border: 1px solid #334155; padding: 12px; border-radius: 8px; color: #f8fafc; font-size: 14px; }
    [data-testid="stChatInput"] { max-width: 600px !important; margin-left: auto !important; margin-right: 20px !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# --- API Anahtarı Başlatma ---
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.sidebar.warning("⚠️ Groq API Anahtarı girilmedi.")
    api_key = st.sidebar.text_input("Groq API Key", type="password")
client = Groq(api_key=api_key) if api_key else None

# --- Yan Menü (Sidebar) ---
st.sidebar.title("🗺️ Müfredat ve Yol Haritası")
st.sidebar.markdown("---")
selected_level = st.sidebar.selectbox("Önce Kur Seçin:", ["A1 - Temel Yapılar (Sıfırdan)", "A2 - Günlük Yaşam", "B1 - Olaylar", "B2 - Profesyonel Akıcılık"])

if st.sidebar.button("🔄 Sohbeti ve Dersi Sıfırla"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown(f"""
<div class="rule-box">
<b>📌 Seçilen Kur:</b> {selected_level}<br><br>
<b>Veritabanı:</b> Aktif 🟢<br>Öğrendiklerin hafızaya kaydediliyor.
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.metric(label="Günlük Seri (Streak)", value=f"{current_streak} Gün 🔥")

# --- Ana Ekran Başlığı ---
st.title("🇩🇪 İnteraktif & Görsel Almanca Akademisi")
st.caption(f"Aktif Modül: {selected_level} | Veri Tabanı ve Kalıcı Hafıza Devrede")

# --- Sekmeli Arayüz Tasarımı ---
tab1, tab2 = st.tabs(["🏛️ Canlandırmalı Ders Odası", "📊 Veritabanı Kelime Havuzu (SRS)"])

with tab1:
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    f"Sen çok disiplinli, 'Mikro-Öğrenme' (Micro-learning) metodunu uygulayan bir Almanca öğretmenisin. "
                    f"Öğrenci şu an '{selected_level}' kurunda.\n\n"
                    "KURALLAR:\n"
                    "1. BİLGİ BOMBARDIMANI YASAK: Her seferinde SADECE BİR kalıp öğret.\n"
                    "2. GÖRSEL DİYALOG: Öğrettiğin kalıbı, EKRANDA İKİ KİŞİ KONUŞUYORMUŞ GİBİ emojilerle canlandır.\n"
                    "3. MİKRO TEST ve ONAY KİLİDİ: Canlandırmadan sonra tek bir pratik sorusu sor ve öğrenci doğru yapmadan diğer kurala geçme."
                )
            }
        ]

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

if prompt := st.chat_input("Mesajınızı buraya yazın (Örn: 'Hazırım, ilk dersi canlandıralım')..."):
    if not client:
        st.error("Lütfen önce API Anahtarınızı girin!")
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
                        messages=st.session_state.messages, model="openai/gpt-oss-120b", stream=True,
                    )
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"API Hatası: {e}")

# --- TAB 2: Dinamik Veritabanı SRS Alanı ---
with tab2:
    st.subheader("Kalıcı Kelime Hafızası (Veritabanı Çıktısı)")
    
    # Yeni kelime ekleme formu
    with st.expander("➕ Veritabanına Yeni Kelime Ekle"):
        with st.form("kelime_ekle_form"):
            yeni_almanca = st.text_input("Almanca Kelime")
            yeni_turkce = st.text_input("Türkçe Anlamı")
            ekle_btn = st.form_submit_button("Sisteme Kaydet")
            
            if ekle_btn and yeni_almanca and yeni_turkce:
                bugun = datetime.now().date()
                c.execute("INSERT INTO vocabulary (almanca, turkce, seviye, next_review) VALUES (?, ?, ?, ?)", (yeni_almanca, yeni_turkce, "A1", bugun))
                conn.commit()
                st.success(f"'{yeni_almanca}' veritabanına kalıcı olarak eklendi!")
                st.rerun()

    # Veritabanından kelimeleri çekip tabloya basma
    c.execute("SELECT almanca, turkce, interval, next_review FROM vocabulary ORDER BY next_review ASC")
    kayitlar = c.fetchall()
    
    # Verileri Streamlit tablosuna uygun formata çevirme
    tablo_verisi = []
    for satir in kayitlar:
        tablo_verisi.append({
            "Almanca": satir[0],
            "Türkçe": satir[1],
            "Aşama (Interval)": f"{satir[2]} Gün",
            "Sonraki Tekrar": satir[3]
        })
    
    if tablo_verisi:
        st.table(tablo_verisi)
    else:
        st.info("Veritabanında henüz kelime yok.")

# Güvenli kapatma
conn.close()

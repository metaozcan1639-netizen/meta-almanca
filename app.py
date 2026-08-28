import streamlit as st
from groq import Groq
import os
import sqlite3
from datetime import datetime, timedelta
from gtts import gTTS
import io

# --- 1. VERİTABANI VE HAZIR A1 KELİME PAKETİ ---
def init_db():
    conn = sqlite3.connect('dil_akademisi.db', check_same_thread=False)
    c = conn.cursor()
    
    # Kelime Havuzu Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            almanca TEXT,
            turkce TEXT,
            seviye TEXT,
            ease_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 1,
            next_review DATE,
            ornek_de TEXT DEFAULT '',
            ornek_tr TEXT DEFAULT ''
        )
    ''')
    
    # Kullanıcı İstatistikleri
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_login DATE,
            total_xp INTEGER DEFAULT 0
        )
    ''')
    
    # İstatistik Tablosu Boşsa Doldur
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        c.execute("INSERT INTO stats (id, streak, last_login, total_xp) VALUES (1, 1, ?, 0)", (bugun,))
    
    # KELİME TABLOSU BOŞSA HAZIR A1 PAKETİNİ YÜKLE
    c.execute("SELECT COUNT(*) FROM vocabulary")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        a1_kelimeler = [
            ("Hallo", "Merhaba", "A1", "Hallo, wie geht es dir?", "Merhaba, nasılsın?"),
            ("Danke", "Teşekkürler", "A1", "Danke für deine Hilfe.", "Yardımın için teşekkürler."),
            ("bitte", "Lütfen / Rica ederim", "A1", "Ein Kaffee, bitte.", "Bir kahve, lütfen."),
            ("Entschuldigung", "Özür dilerim", "A1", "Entschuldigung, wo ist der Bahnhof?", "Afedersiniz, tren istasyonu nerede?"),
            ("Ja", "Evet", "A1", "Ja, das stimmt.", "Evet, bu doğru."),
            ("Nein", "Hayır", "A1", "Nein, ich habe keine Zeit.", "Hayır, zamanım yok."),
            ("der Mann", "Adam", "A1", "Der Mann liest ein Buch.", "Adam bir kitap okuyor."),
            ("die Frau", "Kadın", "A1", "Die Frau trinkt Wasser.", "Kadın su içiyor."),
            ("das Kind", "Çocuk", "A1", "Das Kind spielt im Garten.", "Çocuk bahçede oynuyor."),
            ("das Haus", "Ev", "A1", "Das Haus ist sehr groß.", "Ev çok büyük."),
            ("das Auto", "Araba", "A1", "Er kauft ein neues Auto.", "O yeni bir araba alıyor."),
            ("das Wasser", "Su", "A1", "Ich trinke kaltes Wasser.", "Ben soğuk su içiyorum."),
            ("arbeiten", "Çalışmak", "A1", "Ich arbeite jeden Tag.", "Ben her gün çalışıyorum."),
            ("lernen", "Öğrenmek", "A1", "Wir lernen Deutsch.", "Biz Almanca öğreniyoruz."),
            ("sprechen", "Konuşmak", "A1", "Sprichst du Englisch?", "İngilizce konuşuyor musun?"),
            ("verstehen", "Anlamak", "A1", "Ich verstehe dich nicht.", "Seni anlamıyorum."),
            ("groß", "Büyük", "A1", "Das Zimmer ist groß.", "Oda büyük."),
            ("klein", "Küçük", "A1", "Der Hund ist klein.", "Köpek küçük."),
            ("gut", "İyi", "A1", "Das Essen schmeckt gut.", "Yemek iyi."),
            ("schlecht", "Kötü", "A1", "Das Wetter ist heute schlecht.", "Hava bugün kötü.")
        ]
        for kelime in a1_kelimeler:
            c.execute("INSERT INTO vocabulary (almanca, turkce, seviye, next_review, ornek_de, ornek_tr) VALUES (?, ?, ?, ?, ?, ?)", 
                      (kelime[0], kelime[1], kelime[2], bugun, kelime[3], kelime[4]))
    
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- Günlük Giriş, XP ve Streak ---
bugun = datetime.now().date()
c.execute("SELECT streak, last_login, total_xp FROM stats WHERE id=1")
stat_row = c.fetchone()
current_streak, last_login_str, total_xp = stat_row[0], stat_row[1], stat_row[2]

if last_login_str:
    last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
    if last_login_date == bugun - timedelta(days=1):
        current_streak += 1
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE id=1", (current_streak, bugun))
        conn.commit()
    elif last_login_date < bugun - timedelta(days=1):
        current_streak = 1
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE id=1", (current_streak, bugun))
        conn.commit()

def add_xp(amount):
    global total_xp
    total_xp += amount
    c.execute("UPDATE stats SET total_xp=? WHERE id=1", (total_xp,))
    conn.commit()

# --- Sayfa Konfigürasyonu ve CSS ---
st.set_page_config(page_title="Almanca Görsel & Interaktif Akademi", page_icon="🇩🇪", layout="wide")

st.markdown("""
<style>
    .rule-box { background-color: #0f172a; border: 1px solid #334155; padding: 12px; border-radius: 8px; color: #f8fafc; font-size: 14px; }
    [data-testid="stChatInput"] { max-width: 600px !important; margin-left: auto !important; margin-right: 20px !important; border-radius: 12px !important; }
    .flashcard { background-color: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #3b82f6; text-align: center; min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}
</style>
""", unsafe_allow_html=True)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Groq API Key", type="password")
client = Groq(api_key=api_key) if api_key else None

# --- Yan Menü: Seviye Barı ---
st.sidebar.title("🗺️ Müfredat ve Yol Haritası")
st.sidebar.markdown("---")

levels = ["A1 - Temel Yapılar", "A2 - Günlük Yaşam", "B1 - Olaylar", "B2 - Profesyonel Akıcılık", "C1 - Uzmanlık", "C2 - Anadil"]
selected_level = st.sidebar.selectbox("Hedef Kur Seçin:", levels)

# 1000 XP'de bir kur atlama mantığı
xp_per_level = 1000
current_level_progress = (total_xp % xp_per_level) / xp_per_level
remaining_xp = xp_per_level - (total_xp % xp_per_level)

st.sidebar.progress(current_level_progress, text=f"Seviye İlerlemesi: %{int(current_level_progress*100)}")
st.sidebar.caption(f"Bir sonraki seviyeye geçmek için {remaining_xp} XP kaldı.")

if st.sidebar.button("🔄 Sohbeti ve Dersi Sıfırla"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.metric(label="Toplam Tecrübe", value=f"{total_xp} XP 🌟")
st.sidebar.metric(label="Günlük Seri (Streak)", value=f"{current_streak} Gün 🔥")

st.title("🇩🇪 İnteraktif & Görsel Almanca Akademisi")

tab1, tab2 = st.tabs(["🏛️ Canlandırmalı Ders Odası", "🗂️ Hazır A1 Kelime Kartları"])

# --- TAB 1: Canlandırmalı Ders (Sesli) ---
with tab1:
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": (
                    f"Sen çok disiplinli, 'Mikro-Öğrenme' metodunu uygulayan bir Almanca öğretmenisin. "
                    f"Öğrenci şu an '{selected_level}' kurunda.\n"
                    "1. BİLGİ BOMBARDIMANI YASAK: Her seferinde SADECE BİR kalıp öğret.\n"
                    "2. GÖRSEL DİYALOG: Öğrettiğin kalıbı, iki kişi konuşuyormuş gibi emojilerle canlandır.\n"
                    "3. MİKRO TEST: Canlandırmadan sonra tek bir pratik sorusu sor ve onay verene kadar ilerleme."
                )
            }
        ]

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

if prompt := st.chat_input("Mesajınızı buraya yazın..."):
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
                    
                    if "✅" in full_response or "doğru" in full_response.lower() or "harika" in full_response.lower():
                        add_xp(25)
                        st.success("🎉 +25 XP Kazandın!")
                        
                    # Stremalit'in kendi yerleşik ses oynatıcısı (In-memory, hatasız çalışır)
                    try:
                        tts = gTTS(text=full_response, lang='de')
                        sound_fp = io.BytesIO()
                        tts.write_to_fp(sound_fp)
                        st.audio(sound_fp, format='audio/mp3')
                    except Exception as e:
                        st.caption(f"Ses yüklenemedi: {e}")

                except Exception as e:
                    st.error(f"API Hatası: {e}")

# --- TAB 2: Dönen Flashcard Sistemi (Hazır Liste) ---
with tab2:
    st.subheader("🗂️ A1 Seviyesi Temel Kelimeler")
    st.write("Kartın arkasını görmek için 'Çevir' butonuna basın.")
    
    c.execute("SELECT id, almanca, turkce, ornek_de, ornek_tr FROM vocabulary ORDER BY id ASC")
    kayitlar = c.fetchall()
    
    cols = st.columns(3)
    for index, satir in enumerate(kayitlar):
        col = cols[index % 3]
        card_id = f"card_{satir[0]}"
        
        if card_id not in st.session_state:
            st.session_state[card_id] = "front"
            
        with col:
            st.markdown('<div class="flashcard">', unsafe_allow_html=True)
            if st.session_state[card_id] == "front":
                st.markdown(f"<h3 style='color:#f8fafc;'>{satir[1]}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#94a3b8; font-style:italic;'>\"{satir[3]}\"</p>", unsafe_allow_html=True)
                if st.button("🔄 Çevir", key=f"fbtn_{satir[0]}"):
                    st.session_state[card_id] = "back"
                    st.rerun()
            else:
                st.markdown(f"<h3 style='color:#fbbf24;'>{satir[2]}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#cbd5e1; font-style:italic;'>\"{satir[4]}\"</p>", unsafe_allow_html=True)
                if st.button("🔄 Geri Dön", key=f"bbtn_{satir[0]}"):
                    st.session_state[card_id] = "front"
                    st.rerun()
            st.markdown('</div><br>', unsafe_allow_html=True)

conn.close()

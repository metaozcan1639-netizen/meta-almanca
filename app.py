import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import os
from groq import Groq

# --- 1. VERİTABANI BAĞLANTISI VE KURULUM ---
def init_db():
    conn = sqlite3.connect('dil_akademisi.db', check_same_thread=False)
    c = conn.cursor()
    # Kelimeler
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            almanca TEXT, turkce TEXT, seviye TEXT,
            ease_factor REAL DEFAULT 2.5, interval INTEGER DEFAULT 1,
            next_review DATE, ornek_de TEXT DEFAULT '', ornek_tr TEXT DEFAULT ''
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
    
    # Tablo boşsa varsayılan istatistik oluştur
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        c.execute("INSERT INTO stats (id, streak, last_login, total_xp) VALUES (1, 1, ?, 0)", (bugun,))

    # A1 Kelimeleri yoksa örnek paket yükle
    c.execute("SELECT COUNT(*) FROM vocabulary")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        a1_kelimeler = [
            ("Hallo", "Merhaba", "A1", "Hallo, wie geht es dir?", "Merhaba, nasılsın?"),
            ("Danke", "Teşekkürler", "A1", "Danke für deine Hilfe.", "Yardımın için teşekkürler."),
            ("Entschuldigung", "Özür dilerim", "A1", "Entschuldigung, wo ist der Bahnhof?", "Afedersiniz, istasyon nerede?"),
            ("das Auto", "Araba", "A1", "Er kauft ein neues Auto.", "O yeni bir araba alıyor."),
            ("arbeiten", "Çalışmak", "A1", "Ich arbeite jeden Tag.", "Ben her gün çalışıyorum.")
        ]
        for k in a1_kelimeler:
            c.execute("INSERT INTO vocabulary (almanca, turkce, seviye, next_review, ornek_de, ornek_tr) VALUES (?, ?, ?, ?, ?, ?)", 
                      (k[0], k[1], k[2], bugun, k[3], k[4]))
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- Günlük Giriş ve XP Yönetimi ---
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
    st.session_state.xp = total_xp

# --- Sayfa Konfigürasyonu ---
st.set_page_config(page_title="Almanca Dil Akademisi", page_icon="🇩🇪", layout="wide")

st.markdown("""
<style>
    .metric-box { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px;}
    .header-text { color: #f8fafc; font-size: 24px; font-weight: bold; margin-bottom: 5px; }
    .sub-text { color: #94a3b8; font-size: 14px; }
    .nav-header { font-size: 18px; font-weight: bold; color: #fbbf24; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 5px;}
</style>
""", unsafe_allow_html=True)

# --- API ve Oturum Yönetimi ---
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Groq API Key", type="password")
client = Groq(api_key=api_key) if api_key else None

if "xp" not in st.session_state: st.session_state.xp = total_xp
if "streak" not in st.session_state: st.session_state.streak = current_streak
if "seviye" not in st.session_state: st.session_state.seviye = "A1 - Temel"

# --- Yan Menü (Navigasyon) ---
st.sidebar.markdown('<div class="nav-header">🌍 Akademi Menüsü</div>', unsafe_allow_html=True)
sayfa = st.sidebar.radio(
    "Gitmek istediğiniz bölümü seçin:",
    ["🏠 Ana Ekran (Dashboard)", "📖 Okuma (Lesen)", "🎧 Dinleme (Hören)", "✍️ Yazma (Schreiben)", "🗣️ Konuşma (Sprechen)", "🗂️ Kelime Kartları"]
)

st.sidebar.markdown('<div class="nav-header">⚙️ Ayarlar</div>', unsafe_allow_html=True)
st.session_state.seviye = st.sidebar.selectbox("Aktif Kur:", ["A1 - Temel", "A2 - Başlangıç", "B1 - Orta", "B2 - İleri", "C1 - Uzman", "C2 - Anadil"])

st.sidebar.markdown("---")
st.sidebar.write(f"🔥 **Seri:** {st.session_state.streak} Gün")
st.sidebar.write(f"🌟 **XP:** {st.session_state.xp}")

# ==========================================
# SAYFA İÇERİKLERİ
# ==========================================

if sayfa == "🏠 Ana Ekran (Dashboard)":
    st.title("🇩🇪 Akademi Yönetim Paneli")
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f'<div class="metric-box"><div class="header-text">Mevcut Kur</div><div class="sub-text">{st.session_state.seviye}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-box"><div class="header-text">İlerleme</div><div class="sub-text">%15 (Sonraki kura 850 XP)</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-box"><div class="header-text">Bugünkü Görevler</div><div class="sub-text">0/3 Tamamlandı</div></div>', unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📍 Müfredat Ağacı (A1)")
    with st.expander("Modül 1: Tanışma ve Temel İfadeler", expanded=True):
        st.checkbox("Alfabe ve Telaffuz Kuralları", value=True)
        st.checkbox("Selamlaşma ve Kendini Tanıtma", value=False)
    with st.expander("Modül 2: Temel Gramer (İsimler ve Artikeller)"):
        st.checkbox("Der, Die, Das Mantığı")

elif sayfa == "📖 Okuma (Lesen)":
    st.title("📖 Okuma Odası (Lesen)")
    st.caption("Seviyene uygun dinamik metinler ve anlama testleri.")
    
    if "okuma_metni" not in st.session_state: st.session_state.okuma_metni = ""
    if "okuma_durum" not in st.session_state: st.session_state.okuma_durum = "bekliyor"

    if st.button("📝 Yeni Okuma Parçası ve Soru Getir", use_container_width=True):
        if not client: st.error("API Key gerekli!")
        else:
            with st.spinner("Eğitmen seviyene uygun bir metin hazırlıyor..."):
                prompt = f"Sen profesyonel bir Almanca öğretmenisin. Öğrencinin seviyesi {st.session_state.seviye}. Bu seviyeye gramer ve kelime olarak TAMAMEN uygun, sadece 3-4 cümleden oluşan çok kısa bir Almanca hikaye/metin yaz. Altına da metinle ilgili okuduğunu anlama sorusu sor. Başka hiçbir açıklama yapma. Format şu olsun:\n\nMETİN: [metin buraya]\nSORU: [soru buraya]"
                try:
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}], model="openai/gpt-oss-120b"
                    )
                    st.session_state.okuma_metni = response.choices[0].message.content
                    st.session_state.okuma_durum = "okuyor"
                except Exception as e:
                    st.error(f"API Hatası: {e}")

    if st.session_state.okuma_durum in ["okuyor", "cevaplandi"]:
        st.markdown(f'<div class="metric-box">{st.session_state.okuma_metni}</div>', unsafe_allow_html=True)
        
        if st.session_state.okuma_durum == "okuyor":
            cevap = st.text_input("Yukarıdaki soruya cevabını Almanca olarak yaz:")
            if st.button("Kontrol Et", type="primary"):
                if cevap:
                    with st.spinner("Öğretmen cevabını inceliyor..."):
                        kontrol_prompt = f"Öğrencinin okuduğu metin ve soru şuydu:\n{st.session_state.okuma_metni}\n\nÖğrencinin verdiği cevap: '{cevap}'.\n\nBir öğretmen gibi bu cevabı kontrol et. Hataları varsa nazikçe düzelt. Eğer cevap metne göre büyük oranda doğruysa veya anlatılmak istenen doğruysa, yanıtının en sonuna mutlaka 'DOĞRU' kelimesini büyük harflerle yaz."
                        try:
                            feedback_resp = client.chat.completions.create(
                                messages=[{"role": "user", "content": kontrol_prompt}], model="openai/gpt-oss-120b"
                            )
                            hoca_yorumu = feedback_resp.choices[0].message.content
                            st.session_state.okuma_durum = "cevaplandi"
                            st.session_state.son_yorum = hoca_yorumu
                            
                            if "DOĞRU" in hoca_yorumu:
                                add_xp(25)
                                st.session_state.son_sonuc = "basarili"
                            else:
                                st.session_state.son_sonuc = "hatali"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Hata: {e}")
                else:
                    st.warning("Lütfen kontrol etmeden önce bir cevap yaz.")
                    
        elif st.session_state.okuma_durum == "cevaplandi":
            if st.session_state.son_sonuc == "basarili":
                st.success("🎉 Tebrikler! Metni doğru anladın. +25 XP kazandın.")
            else:
                st.error("Cevabında bazı eksikler veya hatalar var.")
            st.info(f"👩‍🏫 **Öğretmenin Notu:**\n\n{st.session_state.son_yorum.replace('DOĞRU', '')}")

elif sayfa == "🗣️ Konuşma (Sprechen)":
    st.title("🗣️ Konuşma Odası (Sprechen)")
    st.caption("Gerçek hayat senaryoları ve interaktif sohbet.")
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "system", "content": f"Sen profesyonel bir Almanca öğretmenisin. Öğrenci {st.session_state.seviye} seviyesinde. Ona kısa, günlük hayattan bir diyalog başlat. Sadece Almanca konuş ve her seferinde tek bir cümle kurup onun cevap vermesini bekle."}
        ]

    for msg in st.session_state.chat_messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if prompt := st.chat_input("Almanca cevap verin..."):
        if not client: st.error("API Key gerekli!")
        else:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            with st.chat_message("assistant"):
                resp_box = st.empty()
                full_resp = ""
                try:
                    stream = client.chat.completions.create(messages=st.session_state.chat_messages, model="openai/gpt-oss-120b", stream=True)
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_resp += chunk.choices[0].delta.content
                            resp_box.markdown(full_resp + "▌")
                    resp_box.markdown(full_resp)
                    st.session_state.chat_messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"Hata: {e}")

elif sayfa == "🗂️ Kelime Kartları":
    st.title("🗂️ Odaklanmış Kelime Çalışması")
    st.caption("Tüm dikkatini tek bir karta verdiğin özel öğrenme alanı.")
    
    c.execute("SELECT id, almanca, turkce, ornek_de, ornek_tr FROM vocabulary ORDER BY id ASC")
    kelimeler = c.fetchall()
    
    if not kelimeler:
        st.info("Veritabanında henüz kelime yok.")
    else:
        if "kart_index" not in st.session_state: st.session_state.kart_index = 0
        if "kart_yuzu" not in st.session_state: st.session_state.kart_yuzu = "on"

        if st.session_state.kart_index >= len(kelimeler):
            st.success("🎉 Harika! Veritabanındaki tüm kelimeleri tekrar ettin.")
            if st.button("Baştan Başla", use_container_width=True):
                st.session_state.kart_index = 0
                st.rerun()
        else:
            guncel_kelime = kelimeler[st.session_state.kart_index]
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                with st.container(border=True):
                    if st.session_state.kart_yuzu == "on":
                        st.markdown(f"<h1 style='text-align: center; color: #3b82f6;'>{guncel_kelime[1]}</h1>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; font-style: italic; color: #94a3b8;'>{guncel_kelime[3]}</p>", unsafe_allow_html=True)
                        st.write("---")
                        if st.button("🔄 Çevir ve Kontrol Et", use_container_width=True):
                            st.session_state.kart_yuzu = "arka"
                            st.rerun()
                    else:
                        st.markdown(f"<h1 style='text-align: center; color: #fbbf24;'>{guncel_kelime[2]}</h1>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; font-style: italic; color: #cbd5e1;'>{guncel_kelime[4]}</p>", unsafe_allow_html=True)
                        st.write("---")
                        c1, c2 = st.columns(2)
                        if c1.button("🔴 Zordu", use_container_width=True):
                            st.session_state.kart_index += 1
                            st.session_state.kart_yuzu = "on"
                            st.rerun()
                        if c2.button("🟢 Kolaydı", use_container_width=True):
                            add_xp(2) # Kelimeyi bildiği için ufak bir ödül
                            st.session_state.kart_index += 1
                            st.session_state.kart_yuzu = "on"
                            st.rerun()

elif sayfa in ["🎧 Dinleme (Hören)", "✍️ Yazma (Schreiben)"]:
    st.title(sayfa)
    st.info("Bu modülün yapay zeka entegrasyonu (Backend) şu an inşa ediliyor... 🛠️")

conn.close()

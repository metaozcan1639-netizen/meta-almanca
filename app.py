import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import os
import json
import io
from groq import Groq
from gtts import gTTS

# --- 1. VERİTABANI VE SRS (ARALIKLI TEKRAR) KURULUMU ---
def init_db():
    conn = sqlite3.connect('dil_akademisi_v2.db', check_same_thread=False)
    c = conn.cursor()
    
    # Kelime tablosu (SRS güncellendi)
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            almanca TEXT, turkce TEXT, seviye TEXT,
            ease_factor REAL DEFAULT 2.5, interval INTEGER DEFAULT 1,
            next_review DATE, ornek_de TEXT, ornek_tr TEXT
        )
    ''')
    
    # İstatistik tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_login DATE,
            total_xp INTEGER DEFAULT 0
        )
    ''')
    
    # İlk kullanıcıyı oluştur
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        c.execute("INSERT INTO stats (user_id, streak, last_login, total_xp) VALUES (1, 1, ?, 0)", (bugun,))

    # Temel kelimeleri ekle (Eğer boşsa)
    c.execute("SELECT COUNT(*) FROM vocabulary")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        a1_kelimeler = [
            ("die Herausforderung", "Meydan Okuma", "B1", "Das ist eine große Herausforderung.", "Bu büyük bir meydan okuma."),
            ("entwickeln", "Geliştirmek", "B1", "Wir entwickeln eine neue Software.", "Yeni bir yazılım geliştiriyoruz."),
            ("die Wahrscheinlichkeit", "Olasılık", "B2", "Die Wahrscheinlichkeit ist hoch.", "Olasılık yüksek."),
            ("unbedingt", "Kesinlikle/İlla ki", "A2", "Ich muss das unbedingt machen.", "Bunu kesinlikle yapmalıyım."),
            ("der Erfolg", "Başarı", "A2", "Erfolg kommt mit Disziplin.", "Başarı disiplinle gelir.")
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
c.execute("SELECT streak, last_login, total_xp FROM stats WHERE user_id=1")
stat_row = c.fetchone()
current_streak, last_login_str, total_xp = stat_row[0], stat_row[1], stat_row[2]

if last_login_str:
    last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
    if last_login_date == bugun - timedelta(days=1):
        current_streak += 1
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE user_id=1", (current_streak, bugun))
        conn.commit()
    elif last_login_date < bugun - timedelta(days=1):
        current_streak = 1
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE user_id=1", (current_streak, bugun))
        conn.commit()

def add_xp(amount):
    global total_xp
    total_xp += amount
    c.execute("UPDATE stats SET total_xp=? WHERE user_id=1", (total_xp,))
    conn.commit()
    st.session_state.xp = total_xp

# --- Uygulama Arayüzü ve API Ayarları ---
st.set_page_config(page_title="Almanca Akademi Pro", page_icon="🇩🇪", layout="wide")

st.markdown("""
<style>
    .metric-box { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px;}
    .header-text { color: #f8fafc; font-size: 24px; font-weight: bold; margin-bottom: 5px; }
    .sub-text { color: #94a3b8; font-size: 14px; }
    .feedback-box { background-color: #064e3b; padding: 15px; border-radius: 8px; border-left: 5px solid #10b981; margin-top: 10px;}
    .error-box { background-color: #7f1d1d; padding: 15px; border-radius: 8px; border-left: 5px solid #ef4444; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

# API YÖNETİMİ
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("🔑 Groq API Key:", type="password")
client = Groq(api_key=api_key) if api_key else None

MODEL_TEXT = "llama-3.1-70b-versatile"
MODEL_AUDIO = "whisper-large-v3"

if "xp" not in st.session_state: st.session_state.xp = total_xp
if "streak" not in st.session_state: st.session_state.streak = current_streak
if "seviye" not in st.session_state: st.session_state.seviye = "A1"

# --- Yan Menü ---
st.sidebar.title("🌍 Akademi Menüsü")
sayfa = st.sidebar.radio(
    "Modül Seçiniz:",
    ["🏠 Dashboard", "📖 Lesen (Okuma)", "🎧 Hören (Dinleme)", "✍️ Schreiben (Yazma)", "🗣️ Sprechen (Konuşma)", "🗂️ SRS Kelime Kartları"]
)

st.sidebar.markdown("---")
st.session_state.seviye = st.sidebar.selectbox("Hedef Seviye:", ["A1", "A2", "B1", "B2", "C1"])
st.sidebar.markdown(f"🔥 **Seri:** {st.session_state.streak} Gün\n\n🌟 **XP:** {st.session_state.xp}")

# ==========================================
# GÜVENLİ API ÇAĞRISI (JSON Modu)
# ==========================================
def get_json_response(prompt_text):
    if not client:
        st.error("Lütfen API Key girin.")
        return None
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen sadece geçerli bir JSON döndüren bir makinesin. Markdown kullanma."},
                {"role": "user", "content": prompt_text}
            ],
            model=MODEL_TEXT,
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Sistem Hatası: {e}")
        return None

# ==========================================
# SAYFA İÇERİKLERİ
# ==========================================

if sayfa == "🏠 Dashboard":
    st.title("🇩🇪 Akademi Yönetim Paneli")
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f'<div class="metric-box"><div class="header-text">Seviye</div><div class="sub-text">{st.session_state.seviye}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-box"><div class="header-text">Toplam XP</div><div class="sub-text">{st.session_state.xp} XP</div></div>', unsafe_allow_html=True)
    
    # Bugün tekrar edilmesi gereken kelime sayısı
    c.execute("SELECT COUNT(*) FROM vocabulary WHERE next_review <= ?", (bugun,))
    tekrar_sayisi = c.fetchone()[0]
    with col3: st.markdown(f'<div class="metric-box"><div class="header-text">Kelime Tekrarı</div><div class="sub-text">Bugün {tekrar_sayisi} kelime bekliyor</div></div>', unsafe_allow_html=True)
    
    st.write("---")
    st.info("Sol menüden dil modüllerine geçiş yapabilirsiniz. Sistem hatalarınızı analiz edip öğrenme eğrinizi hızlandıracaktır.")

# --- OKUMA (LESEN) ---
elif sayfa == "📖 Lesen (Okuma)":
    st.title("📖 Okuma Odası (Lesen)")
    
    if "okuma_data" not in st.session_state: st.session_state.okuma_data = None

    if st.button("📝 Yeni Metin Üret", use_container_width=True):
        with st.spinner("Metin ve mantıksal soru hazırlanıyor..."):
            prompt = f"""Öğrenci {st.session_state.seviye} seviyesinde. 3 cümlelik Almanca bir metin yaz ve bu metni anlamaya yönelik Almanca bir soru sor. 
            Çıktı SADECE şu JSON formatında olmalı: {{"metin": "almanca metin", "ceviri": "türkçe çeviri", "soru": "almanca soru"}}"""
            data = get_json_response(prompt)
            if data:
                st.session_state.okuma_data = data
                st.session_state.okuma_cevap = None

    if st.session_state.okuma_data:
        st.markdown(f'<div class="metric-box"><h4>{st.session_state.okuma_data["metin"]}</h4><hr><b style="color:#fbbf24;">❓ Soru: {st.session_state.okuma_data["soru"]}</b></div>', unsafe_allow_html=True)
        
        with st.expander("🇹🇷 Metin Çevirisi (Zorlanırsan)"):
            st.write(st.session_state.okuma_data["ceviri"])
            
        cevap = st.text_input("Sorunun cevabını ALMANCA yaz:")
        if st.button("Hocaya Gönder", type="primary"):
            with st.spinner("Analiz ediliyor..."):
                kontrol_prompt = f"""Metin: {st.session_state.okuma_data['metin']}. Soru: {st.session_state.okuma_data['soru']}. Öğrenci Cevabı: {cevap}.
                Bunu değerlendir. Çıktı SADECE şu JSON formatında olsun: {{"basarili": true/false, "gramer_hatalari": "varsa hatalar ve açıklaması", "dogru_versiyon": "Öğrencinin vermek istediği cevabın en kusursuz Almanca hali"}}"""
                sonuc = get_json_response(kontrol_prompt)
                
                if sonuc:
                    if sonuc.get("basarili"):
                        add_xp(25)
                        st.success("🎉 Mükemmel anladın! +25 XP")
                    else:
                        st.error("Cevapta eksik/hata var.")
                    
                    st.info(f"**Hoca Notu:** {sonuc.get('gramer_hatalari', '')}\n\n**Mükemmel Versiyon:** {sonuc.get('dogru_versiyon', '')}")

# --- YAZMA (SCHREIBEN) ---
elif sayfa == "✍️ Schreiben (Yazma)":
    st.title("✍️ Yazma Odası (Schreiben)")
    
    if "yazma_gorev" not in st.session_state: st.session_state.yazma_gorev = None

    if st.button("🎯 Yeni Senaryo Getir", use_container_width=True):
        with st.spinner("Görev atanıyor..."):
            prompt = f"Öğrenci {st.session_state.seviye} seviyesinde. Ona günlük hayattan 1-2 cümlelik Almanca yazma görevi ver. JSON formatı: {{"gorev_tr": "görevin türkçe açıklaması"}}"
            data = get_json_response(prompt)
            if data: st.session_state.yazma_gorev = data.get("gorev_tr")

    if st.session_state.yazma_gorev:
        st.info(f"**Görev:** {st.session_state.yazma_gorev}")
        cevap = st.text_area("Cevabını ALMANCA yaz:")
        
        if st.button("Kontrol Et", type="primary"):
            if cevap:
                with st.spinner("Sentaks ve Gramer taranıyor..."):
                    kontrol_prompt = f"""Görev: {st.session_state.yazma_gorev}. Öğrencinin Almanca metni: {cevap}. 
                    Gramer, artikel ve kelime dizilimi hatalarını bul. Çıktı JSON: {{"puan": 0-100, "analiz": "TÜRKÇE detaylı hata açıklaması", "muttersprachler": "Cümlenin anadil seviyesinde doğal hali"}}"""
                    sonuc = get_json_response(kontrol_prompt)
                    
                    if sonuc:
                        puan = sonuc.get('puan', 0)
                        ifuan = sonuc.get('puan', 0)
                        if puan >= 80:
                            st.success(f"🎉 Puan: {puan}/100. Harika iş! +35 XP")
                            add_xp(35)
                        else:
                            st.warning(f"⚠️ Puan: {puan}/100. Geliştirmen gerekiyor.")
                        
                        st.markdown(f'<div class="error-box"><b>🛠️ Analiz:</b> {sonuc.get("analiz")}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="feedback-box"><b>🇩🇪 Doğal Kullanım:</b> {sonuc.get("muttersprachler")}</div>', unsafe_allow_html=True)

# --- KONUŞMA (SPRECHEN) ---
elif sayfa == "🗣️ Sprechen (Konuşma)":
    st.title("🗣️ Konuşma Odası (Sprechen)")
    st.caption("Mikrofon ile sesini kaydet, yapay zeka seni anlasın ve yanıt versin.")
    
    if "sp_history" not in st.session_state:
        st.session_state.sp_history = []

    # Streamlit Native Audio Input
    audio_value = st.audio_input("Almanca konuş ve gönder:")
    
    if audio_value and client:
        with st.spinner("Sesin metne çevriliyor (Whisper)..."):
            try:
                # Groq Whisper API çağrısı
                transcription = client.audio.transcriptions.create(
                  file=("audio.wav", audio_value.read()),
                  model=MODEL_AUDIO,
                  prompt="German language learning context",
                  response_format="json"
                )
                user_text = transcription.text
                st.session_state.sp_history.append({"role": "user", "content": user_text})
                
                # Hocanın yanıtı
                hoca_prompt = f"Öğrenci Almanca olarak şunu söyledi: '{user_text}'. Sen onun hocasısın. {st.session_state.seviye} seviyesine uygun olarak ona kısaca Almanca cevap ver. JSON Formatı: {{"almanca_cevap": "...", "turkce_ceviri": "..."}}"
                hoca_data = get_json_response(hoca_prompt)
                
                if hoca_data:
                    st.session_state.sp_history.append({"role": "hoca", "de": hoca_data.get("almanca_cevap"), "tr": hoca_data.get("turkce_ceviri")})
                
                add_xp(10) # Konuşma cesareti XP'si
            except Exception as e:
                st.error(f"Ses işleme hatası: {e}")

    # Sohbet Geçmişini Göster
    for msg in st.session_state.sp_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["de"])
                with st.expander("🇹🇷 Çeviriyi Gör"):
                    st.write(msg["tr"])

# --- SRS KELİME KARTLARI (SUPERMEMO-2) ---
elif sayfa == "🗂️ SRS Kelime Kartları":
    st.title("🧠 Akıllı Kelime Hafızası (SRS)")
    st.caption("Sadece bugün tekrar etmen gereken kelimeler gösterilir. Algoritma unutma eğrini hesaplar.")
    
    # BUGÜN TEKRAR EDİLECEKLERİ ÇEK (Asıl sihir burada)
    c.execute("SELECT * FROM vocabulary WHERE next_review <= ?", (bugun,))
    kelimeler = c.fetchall()
    
    if not kelimeler:
        st.success("🎉 Bugünlük tüm tekrarlarını bitirdin! Yeni kelimeler eklemelisin veya yarın tekrar gelmelisin.")
    else:
        if "kart_yuzu" not in st.session_state: st.session_state.kart_yuzu = "on"
        
        guncel_kelime = kelimeler[0]
        k_id, de_kelime, tr_kelime, _, ease_factor, interval, _, ornek_de, ornek_tr = guncel_kelime
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.container(border=True):
                if st.session_state.kart_yuzu == "on":
                    st.markdown(f"<h1 style='text-align: center; color: #3b82f6;'>{de_kelime}</h1>", unsafe_allow_html=True)
                    st.write("---")
                    if st.button("🔄 Çevir", use_container_width=True):
                        st.session_state.kart_yuzu = "arka"
                        st.rerun()
                else:
                    st.markdown(f"<h1 style='text-align: center; color: #fbbf24;'>{tr_kelime}</h1>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; font-style: italic;'>{ornek_de}<br><small style='color:#94a3b8;'>{ornek_tr}</small></p>", unsafe_allow_html=True)
                    st.write("---")
                    
                    c1, c2, c3 = st.columns(3)
                    
                    # SM-2 Mantığı Butonları
                    if c1.button("🔴 Unuttum", use_container_width=True):
                        # Resetle
                        yeni_interval = 1
                        yeni_ease = max(1.3, ease_factor - 0.2)
                        yeni_tarih = bugun + timedelta(days=yeni_interval)
                        c.execute("UPDATE vocabulary SET interval=?, ease_factor=?, next_review=? WHERE id=?", (yeni_interval, yeni_ease, yeni_tarih, k_id))
                        conn.commit()
                        st.session_state.kart_yuzu = "on"
                        st.rerun()
                        
                    if c2.button("🟡 Zorlandım", use_container_width=True):
                        yeni_interval = interval + 1
                        yeni_tarih = bugun + timedelta(days=yeni_interval)
                        c.execute("UPDATE vocabulary SET interval=?, next_review=? WHERE id=?", (yeni_interval, yeni_tarih, k_id))
                        conn.commit()
                        st.session_state.kart_yuzu = "on"
                        st.rerun()

                    if c3.button("🟢 Kolaydı", use_container_width=True):
                        yeni_interval = max(2, int(interval * ease_factor))
                        yeni_ease = ease_factor + 0.1
                        yeni_tarih = bugun + timedelta(days=yeni_interval)
                        c.execute("UPDATE vocabulary SET interval=?, ease_factor=?, next_review=? WHERE id=?", (yeni_interval, yeni_ease, yeni_tarih, k_id))
                        conn.commit()
                        add_xp(5)
                        st.session_state.kart_yuzu = "on"
                        st.rerun()

conn.close()

import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import os
import json
import io
from groq import Groq
from gtts import gTTS

# ==========================================
# 1. VERİTABANI VE SRS (ARALIKLI TEKRAR) MİMARİSİ
# ==========================================
def init_db():
    conn = sqlite3.connect('akademie_master.db', check_same_thread=False)
    c = conn.cursor()
    
    # Kelime Hafıza Sistemi (SuperMemo-2 Altyapısı)
    c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        almanca TEXT, turkce TEXT, seviye TEXT,
        ease_factor REAL DEFAULT 2.5, interval INTEGER DEFAULT 1,
        next_review DATE, ornek_de TEXT, ornek_tr TEXT
    )''')
    
    # Kullanıcı İstatistikleri ve Oyunlaştırma (Gamification)
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        user_id INTEGER PRIMARY KEY,
        streak INTEGER DEFAULT 0,
        last_login DATE,
        total_xp INTEGER DEFAULT 0,
        level TEXT DEFAULT 'A1'
    )''')
    
    # Varsayılan Kullanıcı ve Temel Veri Ataması
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        c.execute("INSERT INTO stats (user_id, streak, last_login, total_xp, level) VALUES (1, 1, ?, 0, 'A1')", (bugun,))
        
        # Sistemi test etmek için başlangıç kelimeleri
        ornek_kelimeler = [
            ("die Herausforderung", "Meydan Okuma", "B1", "Das ist eine große Herausforderung.", "Bu büyük bir meydan okuma."),
            ("unbedingt", "Kesinlikle", "A2", "Ich muss das unbedingt machen.", "Bunu kesinlikle yapmalıyım."),
            ("der Erfolg", "Başarı", "A1", "Erfolg kommt mit Disziplin.", "Başarı disiplinle gelir."),
            ("enttäuscht", "Hayal Kırıklığına Uğramış", "B1", "Ich bin sehr enttäuscht von dir.", "Senden çok hayal kırıklığına uğradım."),
            ("wahrscheinlich", "Muhtemelen", "A2", "Er kommt wahrscheinlich morgen.", "Muhtemelen yarın gelecek.")
        ]
        for k in ornek_kelimeler:
            c.execute("INSERT INTO vocabulary (almanca, turkce, seviye, next_review, ornek_de, ornek_tr) VALUES (?, ?, ?, ?, ?, ?)", 
                      (k[0], k[1], k[2], bugun, k[3], k[4]))
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- Giriş ve XP Sistemi ---
bugun = datetime.now().date()
c.execute("SELECT streak, last_login, total_xp, level FROM stats WHERE user_id=1")
stat_row = c.fetchone()
current_streak, last_login_str, total_xp, current_level = stat_row

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
    st.toast(f"🎉 Harika! +{amount} XP Kazandın!", icon="🔥")

def update_level(new_level):
    c.execute("UPDATE stats SET level=? WHERE user_id=1", (new_level,))
    conn.commit()
    st.session_state.seviye = new_level

# ==========================================
# 2. UI/UX TASARIMI (MODERN CSS)
# ==========================================
st.set_page_config(page_title="Goethe AI - Dil Akademisi", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    /* Global Renkler ve Fontlar */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Modern Kart Tasarımları */
    .dashboard-card { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 15px; border-left: 6px solid #3b82f6; color: white; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); transition: transform 0.2s;}
    .dashboard-card:hover { transform: translateY(-3px); }
    .card-title { font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 600;}
    .card-value { font-size: 32px; font-weight: 800; color: #f8fafc; }
    
    /* Geri Bildirim Kutuları */
    .feedback-success { background-color: #064e3b; padding: 20px; border-radius: 12px; border: 1px solid #059669; margin-top: 15px; color: #d1fae5; }
    .feedback-error { background-color: #450a0a; padding: 20px; border-radius: 12px; border: 1px solid #dc2626; margin-top: 15px; color: #fee2e2; }
    .native-speaker-box { background-color: #1e3a8a; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 5px solid #60a5fa; color: white; font-style: italic;}
    
    /* Yan Menü Tasarımı */
    .sidebar-header { font-size: 22px; font-weight: 800; color: #e2e8f0; text-align: center; margin-bottom: 20px; letter-spacing: -0.5px;}
    .stProgress > div > div > div > div { background-color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. YAPAY ZEKA API MOTORU (KARARLI JSON)
# ==========================================
if "xp" not in st.session_state: st.session_state.xp = total_xp
if "seviye" not in st.session_state: st.session_state.seviye = current_level

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.sidebar.warning("Sistemi başlatmak için API Anahtarınızı girin.")
    api_key = st.sidebar.text_input("🔑 Groq API Key:", type="password")

client = Groq(api_key=api_key) if api_key else None

def get_json_from_llm(system_prompt, user_prompt):
    if not client:
        st.error("Lütfen sol menüden API anahtarını girin.")
        return None
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt + "\nYANITI SADECE GEÇERLİ BİR JSON OLARAK VER. MARKDOWN KULLANMA."},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.7
        )
        # Markdown bloklarını (```json ... ```) temizleme filtresi
        raw_text = response.choices[0].message.content
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI Motoru Hatası: Lütfen tekrar deneyin. Detay: {e}")
        return None

# ==========================================
# 4. YAN MENÜ VE NAVİGASYON
# ==========================================
st.sidebar.markdown('<div class="sidebar-header">🏛️ GOETHE AI</div>', unsafe_allow_html=True)

# Seviye Seçimi
yeni_seviye = st.sidebar.select_slider("Mevcut Seviyeniz:", options=["A1", "A2", "B1", "B2", "C1", "C2"], value=st.session_state.seviye)
if yeni_seviye != st.session_state.seviye:
    update_level(yeni_seviye)

st.sidebar.markdown("---")
sayfa = st.sidebar.radio("📚 ÖĞRENME MODÜLLERİ", ["📊 Dashboard", "📖 Lesen (Okuma)", "🎧 Hören (Dinleme)", "✍️ Schreiben (Yazma)", "🗣️ Sprechen (Konuşma)", "🧠 Akıllı Hafıza (SRS)"])

st.sidebar.markdown("---")
st.sidebar.markdown(f"🔥 **Seri:** {current_streak} Gün\n\n🌟 **Toplam XP:** {st.session_state.xp}")
progress = (st.session_state.xp % 1000) / 1000
st.sidebar.progress(progress, text=f"Sonraki Seviyeye: {1000 - (st.session_state.xp % 1000)} XP")

# ==========================================
# 5. MODÜLLER (SAYFALAR)
# ==========================================

if sayfa == "📊 Dashboard":
    st.title("Hoş Geldin! Öğrenme Durumun")
    st.write("Dil öğrenmek maratondur. Yapay zeka öğretmenin gelişimini adım adım takip ediyor.")
    
    c.execute("SELECT COUNT(*) FROM vocabulary WHERE next_review <= ?", (bugun,))
    bekleyen_kelime = c.fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f'<div class="dashboard-card"><div class="card-title">Hedef Seviye</div><div class="card-value">{st.session_state.seviye}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="dashboard-card"><div class="card-title">Kazanılan XP</div><div class="card-value">{st.session_state.xp}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="dashboard-card"><div class="card-title">Bekleyen Tekrar</div><div class="card-value" style="color:{"#fbbf24" if bekleyen_kelime>0 else "#4ade80"};">{bekleyen_kelime}</div></div>', unsafe_allow_html=True)

    st.markdown("### 🏆 Günlük Görevler")
    t1, t2, t3 = st.columns(3)
    t1.info("📖 1 Okuma Parçası Çöz\n\n**+25 XP**")
    t2.info("🗣️ 3 Cümle Pratik Yap\n\n**+30 XP**")
    t3.info(f"🧠 {bekleyen_kelime} Kelimeyi Tekrar Et\n\n**+10 XP**")

# --- 📖 LESEN (OKUMA) ---
elif sayfa == "📖 Lesen (Okuma)":
    st.header("📖 Okuma ve Anlama (Lesen)")
    st.caption("Seviyene özel oluşturulan metinleri oku, mantıksal soruları yanıtla.")
    
    if "lesen_data" not in st.session_state: st.session_state.lesen_data = None

    if st.button("📝 Yeni Metin Üret", type="primary"):
        with st.spinner("Sana özel bir senaryo yazılıyor..."):
            sys_prompt = "Sen uzman bir Almanca öğretmenisin."
            user_prompt = f"Öğrenci {st.session_state.seviye} seviyesinde. 3 cümlelik ilgi çekici bir Almanca metin yaz. Sonra bu metinle ilgili Almanca bir soru sor. JSON formatı: {{\"metin\": \"...\", \"ceviri\": \"...\", \"soru\": \"...\"}}"
            st.session_state.lesen_data = get_json_from_llm(sys_prompt, user_prompt)
            st.rerun()

    if st.session_state.lesen_data:
        st.markdown(f'<div class="dashboard-card" style="border-left: 6px solid #a855f7;"><h3 style="color:white;">{st.session_state.lesen_data["metin"]}</h3><hr><h5 style="color:#fbbf24;">❓ Soru: {st.session_state.lesen_data["soru"]}</h5></div>', unsafe_allow_html=True)
        
        with st.expander("🇹🇷 Çeviriyi Gör (Sadece zorlanırsan)"):
            st.write(st.session_state.lesen_data["ceviri"])
            
        cevap = st.text_area("Cevabını ALMANCA yaz:")
        if st.button("👩‍🏫 Öğretmene Gönder"):
            if cevap:
                with st.spinner("Cevabın gramer ve anlam açısından inceleniyor..."):
                    sys_prompt = "Sen katı ama cesaretlendirici bir Almanca öğretmenisin."
                    user_prompt = f"Metin: {st.session_state.lesen_data['metin']} Soru: {st.session_state.lesen_data['soru']} Öğrenci Cevabı: {cevap}. Çıktı JSON: {{\"puan\": 0-100, \"durum\": \"basarili/basarisiz\", \"hoca_yorumu\": \"TÜRKÇE detaylı hata analizi\", \"dogru_versiyon\": \"Cevabın kusursuz Almanca hali\"}}"
                    sonuc = get_json_from_llm(sys_prompt, user_prompt)
                    
                    if sonuc:
                        if sonuc.get("puan", 0) >= 70:
                            st.markdown(f'<div class="feedback-success"><b>🎉 Puan: {sonuc.get("puan")}/100</b><br><br><b>👩‍🏫 Yorum:</b> {sonuc.get("hoca_yorumu")}</div>', unsafe_allow_html=True)
                            add_xp(25)
                        else:
                            st.markdown(f'<div class="feedback-error"><b>⚠️ Puan: {sonuc.get("puan")}/100</b><br><br><b>👩‍🏫 Analiz:</b> {sonuc.get("hoca_yorumu")}</div>', unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="native-speaker-box"><b>🇩🇪 Muttersprachler (Anadil) Der ki:</b><br>{sonuc.get("dogru_versiyon")}</div>', unsafe_allow_html=True)

# --- 🎧 HÖREN (DİNLEME) ---
elif sayfa == "🎧 Hören (Dinleme)":
    st.header("🎧 Dinleme Pratiği (Hören)")
    st.caption("Duyduğunu anlama ve yazma becerini geliştir.")
    
    if "horen_data" not in st.session_state: st.session_state.horen_data = None
    
    if st.button("🎧 Yeni Ses Kaydı Oluştur", type="primary"):
        with st.spinner("Stüdyoda ses kaydı hazırlanıyor..."):
            sys_prompt = "Sen uzman bir Almanca öğretmenisin."
            user_prompt = f"Öğrenci {st.session_state.seviye} seviyesinde. Günlük hayattan tek cümlelik bir Almanca ifade yaz. JSON Format: {{\"almanca\": \"...\", \"turkce\": \"...\"}}"
            st.session_state.horen_data = get_json_from_llm(sys_prompt, user_prompt)
            st.rerun()

    if st.session_state.horen_data:
        try:
            tts = gTTS(text=st.session_state.horen_data["almanca"], lang='de')
            sound_fp = io.BytesIO()
            tts.write_to_fp(sound_fp)
            st.audio(sound_fp, format='audio/mp3')
        except Exception as e:
            st.error("Ses motoru başlatılamadı. İnternet bağlantınızı kontrol edin.")
            
        cevap = st.text_input("Duyduğun cümleyi Almanca olarak tam haliyle yaz:")
        if st.button("Kontrol Et"):
            if cevap.strip().lower() == st.session_state.horen_data["almanca"].lower().replace(".", "").replace("!", "").replace("?", "").strip():
                st.success("🎉 Mükemmel! Kulakların çok hassas. +20 XP")
                add_xp(20)
            else:
                st.error("Ufak hatalar var. Tekrar dinle ve karşılaştır.")
                st.info(f"**Doğrusu:** {st.session_state.horen_data['almanca']}\n\n**Çevirisi:** {st.session_state.horen_data['turkce']}")

# --- ✍️ SCHREIBEN (YAZMA) ---
elif sayfa == "✍️ Schreiben (Yazma)":
    st.header("✍️ Kompozisyon ve Yazma (Schreiben)")
    
    if "schreiben_gorev" not in st.session_state: st.session_state.schreiben_gorev = None

    if st.button("🎯 Yeni Senaryo İste", type="primary"):
        with st.spinner("Senaryo kurgulanıyor..."):
            sys_prompt = "Sen yaratıcı bir dil hocasısın."
            user_prompt = f"{st.session_state.seviye} seviyesine uygun, öğrencinin 2-3 cümleyle cevap verebileceği bir durum/görev yarat. Sadece Türkçe yaz. JSON formatı: {{\"gorev\": \"...\"}}"
            data = get_json_from_llm(sys_prompt, user_prompt)
            if data: st.session_state.schreiben_gorev = data.get("gorev")
            st.rerun()

    if st.session_state.schreiben_gorev:
        st.info(f"**Senaryo:** {st.session_state.schreiben_gorev}")
        metin = st.text_area("Buraya Almanca olarak yaz:")
        if st.button("Kalemi Teslim Et"):
            if metin:
                with st.spinner("Gramer, kelime dağarcığı ve yapı inceleniyor..."):
                    sys_prompt = "Sen dilbilgisi uzmanı Alman bir akademisyensin."
                    user_prompt = f"Görev: {st.session_state.schreiben_gorev}. Öğrencinin yazdığı: {metin}. JSON formatında detaylı analiz et: {{\"puan\": 0-100, \"gramer_hatalari\": \"TÜRKÇE açıklama\", \"dogal_versiyon\": \"Anadil seviyesinde Almanca versiyon\"}}"
                    sonuc = get_json_from_llm(sys_prompt, user_prompt)
                    
                    if sonuc:
                        puan = sonuc.get('puan', 0)
                        if puan > 80:
                            st.success(f"🎉 Not: {puan}/100. Kalemin çok kuvvetli! +35 XP")
                            add_xp(35)
                        else:
                            st.warning(f"⚠️ Not: {puan}/100. Gelişime açık.")
                        
                        st.markdown(f"**🛠️ Öğretmenin Düzeltmeleri:** {sonuc.get('gramer_hatalari')}")
                        st.markdown(f'<div class="native-speaker-box"><b>🇩🇪 En Şık İfade Ediliş Biçimi:</b><br>{sonuc.get("dogal_versiyon")}</div>', unsafe_allow_html=True)

# --- 🗣️ SPRECHEN (KONUŞMA) ---
elif sayfa == "🗣️ Sprechen (Konuşma)":
    st.header("🗣️ Konuşma Odası (Sprechen)")
    st.write("Yapay zeka öğretmeninle gerçek zamanlı sesli diyalog kur.")
    
    if "sp_history" not in st.session_state: st.session_state.sp_history = []
    
    audio_bytes = st.audio_input("Mikrofona tıkla ve Almanca konuş:")
    
    if audio_bytes and client:
        with st.spinner("Sesin metne çevriliyor (Whisper STT)..."):
            try:
                transcription = client.audio.transcriptions.create(
                  file=("audio.wav", audio_bytes.read()),
                  model="whisper-large-v3",
                  prompt="German conversation",
                  response_format="json"
                )
                user_text = transcription.text
                st.session_state.sp_history.append({"role": "user", "content": user_text})
                
                # Hocanın cevabı
                sys_prompt = "Sen bir Alman dil partnerisin. Kısa ve samimi cevaplar ver."
                user_prompt = f"Ben (Öğrenci - {st.session_state.seviye}): {user_text}. Bana Almanca cevap ver. JSON Formatı: {{\"de\": \"Almanca cevap\", \"tr\": \"Türkçe çevirisi\"}}"
                hoca_data = get_json_from_llm(sys_prompt, user_prompt)
                
                if hoca_data:
                    st.session_state.sp_history.append({"role": "ai", "de": hoca_data.get("de"), "tr": hoca_data.get("tr")})
                    add_xp(15)
            except Exception as e:
                st.error(f"Mikrofon erişimi veya çeviri hatası: {e}")

    for msg in reversed(st.session_state.sp_history):
        if msg["role"] == "user":
            st.markdown(f'<div style="text-align: right; background-color: #334155; padding: 10px; border-radius: 10px; margin: 5px 0 5px 20%;">🗣️ <b>Sen:</b> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin: 5px 20% 5px 0; border-left: 5px solid #3b82f6;">👩‍🏫 <b>Hoca:</b> {msg["de"]}<br><small style="color: #94a3b8;">🇹🇷 {msg["tr"]}</small></div>', unsafe_allow_html=True)

# --- 🧠 AKILLI HAFIZA (SRS) ---
elif sayfa == "🧠 Akıllı Hafıza (SRS)":
    st.header("🧠 SuperMemo-2 Kelime Tekrarı")
    st.write("Beyninin unutma eğrisini hackleyerek kelimeleri kalıcı hafızana atıyoruz.")
    
    c.execute("SELECT * FROM vocabulary WHERE next_review <= ?", (bugun,))
    kelimeler = c.fetchall()
    
    if not kelimeler:
        st.markdown('<div class="dashboard-card" style="text-align:center; border-left: 6px solid #4ade80;"><h2>🎉 Harika!</h2><p>Bugünlük tüm kelime tekrarlarını bitirdin. Yarın tekrar gel!</p></div>', unsafe_allow_html=True)
    else:
        if "kart_yuzu" not in st.session_state: st.session_state.kart_yuzu = "on"
        k_id, de_kelime, tr_kelime, _, ease_factor, interval, _, ornek_de, ornek_tr = kelimeler[0]
        
        st.progress(1.0, text=f"Bugün kalan kelime: {len(kelimeler)}")
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div style="background-color: #1e293b; padding: 40px; border-radius: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">', unsafe_allow_html=True)
            if st.session_state.kart_yuzu == "on":
                st.markdown(f"<h1 style='color: #60a5fa; font-size: 40px;'>{de_kelime}</h1>", unsafe_allow_html=True)
                st.markdown('</div><br>', unsafe_allow_html=True)
                if st.button("🔄 Anlamını Göster", use_container_width=True, type="primary"):
                    st.session_state.kart_yuzu = "arka"
                    st.rerun()
            else:
                st.markdown(f"<h2 style='color: #fbbf24;'>{tr_kelime}</h2>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: #cbd5e1; font-style: italic; margin-top: 15px;'>\"{ornek_de}\"<br><small>{ornek_tr}</small></p>", unsafe_allow_html=True)
                st.markdown('</div><br>', unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if c1.button("🔴 Unuttum (1 Gün)", use_container_width=True):
                    c.execute("UPDATE vocabulary SET interval=1, ease_factor=?, next_review=? WHERE id=?", (max(1.3, ease_factor - 0.2), bugun + timedelta(days=1), k_id))
                    conn.commit(); st.session_state.kart_yuzu = "on"; st.rerun()
                if c2.button("🟡 Zordu", use_container_width=True):
                    c.execute("UPDATE vocabulary SET interval=?, next_review=? WHERE id=?", (interval + 1, bugun + timedelta(days=interval + 1), k_id))
                    conn.commit(); st.session_state.kart_yuzu = "on"; st.rerun()
                if c3.button("🟢 Kolaydı", use_container_width=True):
                    yeni_interval = max(2, int(interval * ease_factor))
                    c.execute("UPDATE vocabulary SET interval=?, ease_factor=?, next_review=? WHERE id=?", (yeni_interval, ease_factor + 0.1, bugun + timedelta(days=yeni_interval), k_id))
                    conn.commit(); add_xp(5); st.session_state.kart_yuzu = "on"; st.rerun()

conn.close()

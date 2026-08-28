import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import os
import re
import io
from groq import Groq
from gtts import gTTS

# --- 1. VERİTABANI BAĞLANTISI VE KURULUM ---
def init_db():
    conn = sqlite3.connect('dil_akademisi.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            almanca TEXT, turkce TEXT, seviye TEXT,
            ease_factor REAL DEFAULT 2.5, interval INTEGER DEFAULT 1,
            next_review DATE, ornek_de TEXT DEFAULT '', ornek_tr TEXT DEFAULT ''
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_login DATE,
            total_xp INTEGER DEFAULT 0
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        c.execute("INSERT INTO stats (id, streak, last_login, total_xp) VALUES (1, 1, ?, 0)", (bugun,))

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
    with col3: st.markdown(f'<div class="metric-box"><div class="header-text">Durum</div><div class="sub-text">Akademi Aktif 🟢</div></div>', unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📍 Modüller")
    st.info("Sol menüden beceri odalarını seçerek çalışmaya başlayabilirsin. Okuma, Dinleme, Yazma ve Konuşma odalarının hepsi tam entegre çalışmaktadır.")

elif sayfa == "📖 Okuma (Lesen)":
    st.title("📖 Okuma Odası (Lesen)")
    st.caption("Seviyene uygun dinamik metinler ve anlama testleri.")
    
    if "okuma_metni" not in st.session_state: st.session_state.okuma_metni = ""
    if "okuma_ceviri" not in st.session_state: st.session_state.okuma_ceviri = ""
    if "okuma_soru" not in st.session_state: st.session_state.okuma_soru = ""
    if "okuma_durum" not in st.session_state: st.session_state.okuma_durum = "bekliyor"

    if st.button("📝 Yeni Okuma Parçası ve Soru Getir", use_container_width=True):
        if not client: st.error("API Key gerekli!")
        else:
            with st.spinner("Metin hazırlanıyor..."):
                prompt = f"Sen profesyonel bir Almanca öğretmenisin. Öğrenci {st.session_state.seviye} seviyesinde, dili yeni öğreniyor. Bu seviyeye uygun, 2 cümleden oluşan basit bir Almanca metin yaz. Altına da basit bir Almanca soru sor. Format ŞU OLMALI:\n\nMETİN: [Almanca metin]\nÇEVİRİ: [Türkçe çevirisi]\nSORU: [Almanca soru]"
                try:
                    response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="openai/gpt-oss-120b")
                    icerik = response.choices[0].message.content
                    metin_match = re.search(r"METİN:\s*(.*?)(?=ÇEVİRİ:)", icerik, re.DOTALL)
                    ceviri_match = re.search(r"ÇEVİRİ:\s*(.*?)(?=SORU:)", icerik, re.DOTALL)
                    soru_match = re.search(r"SORU:\s*(.*)", icerik, re.DOTALL)
                    
                    st.session_state.okuma_metni = metin_match.group(1).strip() if metin_match else icerik
                    st.session_state.okuma_ceviri = ceviri_match.group(1).strip() if ceviri_match else "Çeviri bulunamadı."
                    st.session_state.okuma_soru = soru_match.group(1).strip() if soru_match else ""
                    st.session_state.okuma_durum = "okuyor"
                except Exception as e:
                    st.error(f"Hata: {e}")

    if st.session_state.okuma_durum in ["okuyor", "cevaplandi"]:
        st.markdown(f'<div class="metric-box"><h5 style="color:#f8fafc;">🇩🇪 {st.session_state.okuma_metni}</h5><br><b style="color:#fbbf24;">❓ Soru: {st.session_state.okuma_soru}</b></div>', unsafe_allow_html=True)
        
        with st.expander("🇹🇷 Metnin ve Sorunun Çevirisini Göster"):
            st.info(st.session_state.okuma_ceviri)
        
        if st.session_state.okuma_durum == "okuyor":
            cevap = st.text_input("Yukarıdaki soruya cevabını TÜRKÇE olarak yaz:")
            if st.button("Kontrol Et", type="primary"):
                if cevap:
                    with st.spinner("Öğretmen inceliyor..."):
                        kontrol_prompt = f"Metin: {st.session_state.okuma_metni}\nSoru: {st.session_state.okuma_soru}\nÖğrencinin TÜRKÇE cevabı: '{cevap}'.\nDoğru mu anlamış? Doğruysa sonuna 'DOĞRU' yaz, kısaca açıkla."
                        try:
                            feedback_resp = client.chat.completions.create(messages=[{"role": "user", "content": kontrol_prompt}], model="openai/gpt-oss-120b")
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
                    st.warning("Lütfen cevap yaz.")
                    
        elif st.session_state.okuma_durum == "cevaplandi":
            if st.session_state.son_sonuc == "basarili": st.success("🎉 Tebrikler! +25 XP")
            else: st.error("Cevabında eksikler var.")
            st.info(f"👩‍🏫 **Not:**\n\n{st.session_state.son_yorum.replace('DOĞRU', '')}")

elif sayfa == "🎧 Dinleme (Hören)":
    st.title("🎧 Dinleme Odası (Hören)")
    st.caption("Ekranda metin yok! Duyduğunu anlama pratiği.")
    
    if "dinleme_metni" not in st.session_state: st.session_state.dinleme_metni = ""
    if "dinleme_ceviri" not in st.session_state: st.session_state.dinleme_ceviri = ""
    if "dinleme_durum" not in st.session_state: st.session_state.dinleme_durum = "bekliyor"

    if st.button("🎧 Yeni Ses Getir", use_container_width=True):
        if not client: st.error("API Key gerekli!")
        else:
            with st.spinner("Ses dosyası hazırlanıyor..."):
                prompt = f"Sen Almanca öğretmenisin. Öğrenci {st.session_state.seviye} seviyesinde. SADECE 1 cümlelik çok basit bir dinleme metni yaz. Format ŞART:\nMETİN: [Almanca cümle]\nÇEVİRİ: [Türkçe çeviri]"
                try:
                    response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="openai/gpt-oss-120b")
                    icerik = response.choices[0].message.content
                    metin_match = re.search(r"METİN:\s*(.*?)(?=ÇEVİRİ:)", icerik, re.DOTALL)
                    ceviri_match = re.search(r"ÇEVİRİ:\s*(.*)", icerik, re.DOTALL)
                    
                    st.session_state.dinleme_metni = metin_match.group(1).strip() if metin_match else "Hallo, wie geht es dir?"
                    st.session_state.dinleme_ceviri = ceviri_match.group(1).strip() if ceviri_match else "Merhaba, nasılsın?"
                    st.session_state.dinleme_durum = "dinliyor"
                except Exception as e:
                    st.error(f"Hata: {e}")

    if st.session_state.dinleme_durum in ["dinliyor", "cevaplandi"]:
        try:
            tts = gTTS(text=st.session_state.dinleme_metni, lang='de')
            sound_fp = io.BytesIO()
            tts.write_to_fp(sound_fp)
            st.audio(sound_fp, format='audio/mp3')
        except Exception as e:
            st.warning("Ses oluşturulamadı. gTTS kütüphanesini kontrol edin.")

        with st.expander("📝 Gizli Transkripti ve Çeviriyi Göster (Zorlanırsan Tıkla)"):
            st.write(f"**🇩🇪 Almanca:** {st.session_state.dinleme_metni}")
            st.write(f"**🇹🇷 Türkçe:** {st.session_state.dinleme_ceviri}")
            
        if st.session_state.dinleme_durum == "dinliyor":
            cevap = st.text_input("Duyduğun cümleyi ister Almanca ister Türkçe çevirisiyle yaz:")
            if st.button("Kontrol Et", type="primary"):
                if cevap:
                    with st.spinner("Öğretmen inceliyor..."):
                        kontrol_prompt = f"Orijinal Metin: {st.session_state.dinleme_metni}\nÇevirisi: {st.session_state.dinleme_ceviri}\nÖğrencinin duyup yazdığı: '{cevap}'.\nDoğru mu anlamış? Doğruysa sonuna 'DOĞRU' yaz, kısaca Türkçe açıkla."
                        feedback_resp = client.chat.completions.create(messages=[{"role": "user", "content": kontrol_prompt}], model="openai/gpt-oss-120b")
                        hoca_yorumu = feedback_resp.choices[0].message.content
                        st.session_state.dinleme_durum = "cevaplandi"
                        st.session_state.son_dinleme_yorum = hoca_yorumu
                        if "DOĞRU" in hoca_yorumu:
                            add_xp(30)
                            st.session_state.son_dinleme_sonuc = "basarili"
                        else:
                            st.session_state.son_dinleme_sonuc = "hatali"
                        st.rerun()
                else:
                    st.warning("Lütfen cevap yaz.")
                    
        elif st.session_state.dinleme_durum == "cevaplandi":
            if st.session_state.son_dinleme_sonuc == "basarili": st.success("🎉 Kulağın çok iyi! +30 XP")
            else: st.error("Tekrar dinlemelisin.")
            st.info(f"👩‍🏫 **Not:**\n\n{st.session_state.son_dinleme_yorum.replace('DOĞRU', '')}")

elif sayfa == "✍️ Yazma (Schreiben)":
    st.title("✍️ Yazma Odası (Schreiben)")
    st.caption("Sana verilen senaryoya göre Almanca yazılar yaz, hoca notlandırsın.")

    if "yazma_gorev" not in st.session_state: st.session_state.yazma_gorev = ""
    if "yazma_durum" not in st.session_state: st.session_state.yazma_durum = "bekliyor"

    if st.button("📝 Yeni Görev Getir", use_container_width=True):
        if not client: st.error("API Key gerekli!")
        else:
            with st.spinner("Görev oluşturuluyor..."):
                prompt = f"Öğrenci {st.session_state.seviye} seviyesinde. Ona pratik yapması için günlük hayattan basit bir YAZMA GÖREVİ ver. (Örn: 'Bir kafedesin, 1 kahve ve 1 su siparişi ver'). SADECE Türkçe olarak görevi yaz. Format: GÖREV: [görev metni]"
                response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="openai/gpt-oss-120b")
                st.session_state.yazma_gorev = response.choices[0].message.content.replace("GÖREV:", "").strip()
                st.session_state.yazma_durum = "yaziyor"

    if st.session_state.yazma_durum in ["yaziyor", "cevaplandi"]:
        st.info(f"🎯 **Görev:** {st.session_state.yazma_gorev}")
        
        if st.session_state.yazma_durum == "yaziyor":
            cevap = st.text_area("Cevabını ALMANCA olarak yaz:")
            if st.button("Öğretmene Gönder", type="primary"):
                if cevap:
                    with st.spinner("Öğretmen okuyor..."):
                        kontrol_prompt = f"Görev şuydu: {st.session_state.yazma_gorev}\nÖğrencinin yazdığı Almanca: '{cevap}'.\nÖğretmen gibi hatalarını düzelt, grameri Türkçe açıkla. Genel olarak anlaşılabiliyorsa sonuna 'DOĞRU' yaz."
                        feedback_resp = client.chat.completions.create(messages=[{"role": "user", "content": kontrol_prompt}], model="openai/gpt-oss-120b")
                        hoca_yorumu = feedback_resp.choices[0].message.content
                        st.session_state.yazma_durum = "cevaplandi"
                        st.session_state.son_yazma_yorum = hoca_yorumu
                        if "DOĞRU" in hoca_yorumu:
                            add_xp(35)
                            st.session_state.son_yazma_sonuc = "basarili"
                        else:
                            st.session_state.son_yazma_sonuc = "hatali"
                        st.rerun()
                else:
                    st.warning("Boş kağıt veremezsin!")
                    
        elif st.session_state.yazma_durum == "cevaplandi":
            if st.session_state.son_yazma_sonuc == "basarili": st.success("🎉 Çok iyi ifade ettin! +35 XP")
            else: st.error("Daha iyi olabilir, hatalarına dikkat et.")
            st.info(f"👩‍🏫 **Öğretmenin Düzeltmeleri:**\n\n{st.session_state.son_yazma_yorum.replace('DOĞRU', '')}")

elif sayfa == "🗣️ Konuşma (Sprechen)":
    st.title("🗣️ Konuşma Odası (Sprechen)")
    st.caption("Türkçe yardım isteyebilir veya diyaloğu sürdürebilirsin. Çeviriler gizlidir.")
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "system", "content": f"Sen arkadaş canlısı, iki dilli (Türkçe-Almanca) bir öğretmensin. Öğrenci {st.session_state.seviye} seviyesinde. Ona kısa diyaloglar kuracaksın. YANIT FORMATIN ŞARTTIR:\nALMANCA: [Sadece Almanca cümle]\nÇEVİRİ: [Türkçe çevirisi veya Türkçe açıklama]. Eğer öğrenci senden Türkçe yardım isterse, 'ÇEVİRİ' kısmında ona Türkçe açıkla, 'ALMANCA' kısmında onu motive edecek basit bir Almanca cümle kur."}
        ]
        # Yapay zekayı tetikleyip ilk soruyu sorduruyoruz
        response = client.chat.completions.create(messages=st.session_state.chat_messages, model="openai/gpt-oss-120b")
        st.session_state.chat_messages.append({"role": "assistant", "content": response.choices[0].message.content})

    # Sohbet geçmişini çizdirme (Çevirileri ayırarak)
    for msg in st.session_state.chat_messages:
        if msg["role"] == "assistant":
            if "ÇEVİRİ:" in msg["content"]:
                parts = msg["content"].split("ÇEVİRİ:")
                almanca_kisim = parts[0].replace("ALMANCA:", "").strip()
                turkce_kisim = parts[1].strip()
                
                with st.chat_message("assistant"):
                    st.write(almanca_kisim)
                    with st.expander("🇹🇷 Çeviriyi / Açıklamayı Göster"):
                        st.info(turkce_kisim)
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])
        elif msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])

    if prompt := st.chat_input("Almanca yaz veya Türkçe yardım iste..."):
        if not client: st.error("API Key gerekli!")
        else:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            with st.spinner("Hoca yazıyor..."):
                try:
                    # Stream kapalı, arayüzün bozulmaması için cevabı tam alıp basıyoruz
                    response = client.chat.completions.create(messages=st.session_state.chat_messages, model="openai/gpt-oss-120b")
                    full_resp = response.choices[0].message.content
                    st.session_state.chat_messages.append({"role": "assistant", "content": full_resp})
                    st.rerun()
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
                            add_xp(2)
                            st.session_state.kart_index += 1
                            st.session_state.kart_yuzu = "on"
                            st.rerun()

conn.close()

import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import os
import json
import io
import re
from groq import Groq
from gtts import gTTS

# ==========================================
# 0. SİSTEM YAPILANDIRMASI VE CSS MİMARİSİ
# ==========================================
st.set_page_config(page_title="Goethe AI - Dil Akademisi Pro", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Playfair+Display:ital,wght@0,700;1,400&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #f1f5f9; background-color: #0f172a; }
    
    /* Modern Kart Tasarımları */
    .dashboard-card { background: linear-gradient(145deg, #1e293b, #0f172a); padding: 25px; border-radius: 16px; border: 1px solid #334155; border-left: 6px solid #3b82f6; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); transition: transform 0.2s, box-shadow 0.2s; margin-bottom: 20px;}
    .dashboard-card:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4); }
    .card-title { font-size: 15px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; font-weight: 600;}
    .card-value { font-size: 38px; font-weight: 800; color: #f8fafc; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);}
    
    /* İlerleme ve Modül Başlıkları */
    .module-header { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 700; color: #e2e8f0; margin-bottom: 5px;}
    .module-subtitle { font-size: 16px; color: #64748b; margin-bottom: 25px; font-weight: 300;}
    
    /* Geri Bildirim Kutuları */
    .feedback-success { background-color: rgba(6, 78, 59, 0.4); padding: 25px; border-radius: 12px; border: 1px solid #10b981; border-left: 6px solid #059669; margin-top: 20px; color: #ecfdf5; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
    .feedback-error { background-color: rgba(69, 10, 10, 0.4); padding: 25px; border-radius: 12px; border: 1px solid #ef4444; border-left: 6px solid #dc2626; margin-top: 20px; color: #fef2f2; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
    .feedback-warning { background-color: rgba(120, 53, 15, 0.4); padding: 25px; border-radius: 12px; border: 1px solid #f59e0b; border-left: 6px solid #d97706; margin-top: 20px; color: #fffbeb; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
    
    .native-speaker-box { background-color: rgba(30, 58, 138, 0.3); padding: 20px; border-radius: 10px; margin-top: 20px; border-left: 6px solid #3b82f6; color: #eff6ff; font-family: 'Inter', sans-serif;}
    .native-label { font-size: 12px; color: #93c5fd; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; margin-bottom: 8px; display: block;}
    .native-text { font-size: 18px; font-weight: 400; font-style: italic;}
    
    /* Eğitim Odası Tasarımı */
    .lesson-box { background: rgba(15, 23, 42, 0.6); border: 1px solid #334155; border-radius: 12px; padding: 35px; margin-bottom: 20px; border-top: 4px solid #8b5cf6; min-height: 400px;}
    
    /* Hatasız Kapsayıcılı Flashcard Tasarımı */
    .flashcard { 
        background: linear-gradient(180deg, #1e293b, #0f172a); 
        border: 2px solid #3b82f6; 
        border-radius: 20px; 
        padding: 30px; 
        text-align: center; 
        box-shadow: 0 15px 30px rgba(0,0,0,0.4); 
        min-height: 380px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        align-items: center;
        position: relative;
    }
    
    .css-1d391kg { background-color: #0b1120; }
    .sidebar-header { font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; color: #f8fafc; text-align: center; margin-bottom: 30px; letter-spacing: 1px; border-bottom: 1px solid #1e293b; padding-bottom: 15px;}
    
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KATI CEFR KALİBRASYON MATRİSİ
# ==========================================
CEFR_RULES = {
    "A1.1": "SADECE en temel kelimeleri kullan. Yalnızca şimdiki zaman (Präsens) ve sein/haben fiillerini kullan. Asla karmaşık yan cümle (Nebensatz) kurma.",
    "A1.2": "Akkusativ (ismin -i hali), modal fiiller ve Perfekt (yakın geçmiş zaman) kullanabilirsin. Basit bağlaçlar (und, oder, aber) ile sınırlandır.",
    "A2.1": "Dativ, yer yön bildiren edatlar (Wechselpräpositionen) ve geçmiş zamanda Präteritum (sadece sein/haben için) kullan.",
    "A2.2": "Refleksif fiiller, basit yan cümleler (weil, dass, wenn), Futur I ve sıfatlarda derecelendirme (Komparativ) kullan.",
    "B1.1": "Präteritum (tüm fiillerle), Konjunktiv II (kibar istekler), ve Relativsätze (ilgi cümleleri) yapılarını aktif olarak kullan.",
    "B1.2": "Passiv (edilgen çatı), sebep bildiren edatlar (trotz, wegen) ve Partizip I/II kullan. Dil seviyesi orta-ileri olmalı.",
    "B2.1": "Soyut kavramlar, karmaşık bağlaçlar (je... desto) ve N-Deklination kullan. Cümleler uzun ve mantıksal olarak birbirine bağlı olmalı.",
    "B2.2": "İleri düzey tartışma dili, nominal stil (isimleştirme) ve Konjunktiv I (dolaylı anlatım) başlangıcı kullan.",
    "C1": "Akademik ve edebi dil, karmaşık sentaks, Funktionsverbgefüge kullan. Anadil akıcılığında ve yüksek resmiyette olmalı.",
    "C2": "Alman deyimleri (Redewendungen), kültürel nüanslar, edebi sanatlar ve bölgesel ifadeler kullan. Dilin sınırlarını zorla."
}

# ==========================================
# 2. VERİTABANI VE İLERİ DÜZEY SRS MİMARİSİ
# ==========================================
def init_db():
    conn = sqlite3.connect('akademie_master_pro.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        almanca TEXT UNIQUE, turkce TEXT, seviye TEXT,
        ease_factor REAL DEFAULT 2.5, interval INTEGER DEFAULT 1,
        next_review DATE, ornek_de TEXT, ornek_tr TEXT,
        correct_streak INTEGER DEFAULT 0, last_reviewed DATE
    )''')
    
    try:
        c.execute("ALTER TABLE vocabulary ADD COLUMN emoji TEXT DEFAULT '💠'")
    except sqlite3.OperationalError:
        pass 
    
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        user_id INTEGER PRIMARY KEY,
        streak INTEGER DEFAULT 0,
        last_login DATE,
        total_xp INTEGER DEFAULT 0,
        level TEXT DEFAULT 'A1.1',
        modules_completed INTEGER DEFAULT 0,
        accuracy_rate REAL DEFAULT 100.0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS performance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        module_name TEXT,
        score INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        bugun = datetime.now().date()
        c.execute("INSERT INTO stats (user_id, streak, last_login, total_xp, level) VALUES (1, 1, ?, 0, 'A1.1')", (bugun,))
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

bugun = datetime.now().date()
c.execute("SELECT streak, last_login, total_xp, level, accuracy_rate FROM stats WHERE user_id=1")
stat_row = c.fetchone()
current_streak, last_login_str, total_xp, current_level, accuracy_rate = stat_row

if last_login_str:
    last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
    if last_login_date == bugun - timedelta(days=1):
        current_streak += 1
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE user_id=1", (current_streak, bugun))
    elif last_login_date < bugun - timedelta(days=1):
        current_streak = 1
        c.execute("UPDATE stats SET streak=?, last_login=? WHERE user_id=1", (current_streak, bugun))
    conn.commit()

def update_performance(module, score):
    global total_xp, accuracy_rate
    xp_earned = score // 2
    total_xp += xp_earned
    new_accuracy = (accuracy_rate * 0.9) + (score * 0.1)
    
    c.execute("INSERT INTO performance_logs (user_id, module_name, score) VALUES (1, ?, ?)", (module, score))
    c.execute("UPDATE stats SET total_xp=?, accuracy_rate=?, modules_completed=modules_completed+1 WHERE user_id=1", (total_xp, new_accuracy))
    conn.commit()
    st.session_state.xp = total_xp
    if xp_earned > 0:
        st.toast(f"🎉 {module} tamamlandı! +{xp_earned} XP Kazandın!", icon="✨")

def update_level(new_level):
    c.execute("UPDATE stats SET level=? WHERE user_id=1", (new_level,))
    conn.commit()
    st.session_state.seviye = new_level
    st.toast(f"Seviye hedefin {new_level} olarak güncellendi.", icon="📈")

# ==========================================
# 3. YAPAY ZEKA API MOTORU
# ==========================================
if "xp" not in st.session_state: 
    st.session_state.xp = total_xp
if "seviye" not in st.session_state: 
    st.session_state.seviye = current_level
if "gunun_konusu" not in st.session_state: 
    st.session_state.gunun_konusu = ""

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    with st.sidebar:
        st.warning("⚠️ Sistemi başlatmak için API anahtarınızı girin.")
        api_key = st.text_input("🔑 API Key:", type="password", key="api_key_input")
        if not api_key:
            st.stop()

client = Groq(api_key=api_key)

def get_json_from_llm(system_prompt, user_prompt, model="openai/gpt-oss-120b"):
    cefr_kurali = CEFR_RULES.get(st.session_state.seviye, "")
    ders_kurali = f"\nÖğrencinin bugünkü aktif ders konusu: '{st.session_state.gunun_konusu}'. İçeriği kesinlikle bu konuya ve kurallarına odakla." if st.session_state.gunun_konusu else ""
    full_system_prompt = f"{system_prompt}\n\nDİKKAT! Öğrenci {st.session_state.seviye} seviyesinde. KESİN KURAL: {cefr_kurali}{ders_kurali}"
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": full_system_prompt + "\n\nCRITICAL INSTRUCTION: You MUST return ONLY valid, raw JSON. Do not use Markdown code blocks. Do not include conversational text."},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        raw_content = response.choices[0].message.content.strip()
        clean_content = re.sub(r"^```json\s*", "", raw_content, flags=re.IGNORECASE)
        clean_content = re.sub(r"^```\s*", "", clean_content)
        clean_content = re.sub(r"\s*```$", "", clean_content)
        
        return json.loads(clean_content)
    
    except Exception as e:
        st.error(f"AI İletişim Hatası: {e}")
        return None

# ==========================================
# 4. YAN MENÜ (SIDEBAR) VE İSTATİKLER
# ==========================================
st.sidebar.markdown('<div class="sidebar-header">🏛️ GOETHE AI<br><span style="font-size:12px; font-weight:400; color:#94a3b8; font-family:Inter;">Die Sprachakademie</span></div>', unsafe_allow_html=True)

progress_val = (st.session_state.xp % 2000) / 2000
st.sidebar.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.5); padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #334155;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="color: #94a3b8; font-size: 13px;">Seri</span>
            <span style="color: #fbbf24; font-weight: bold;">🔥 {current_streak} Gün</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #94a3b8; font-size: 13px;">XP</span>
            <span style="color: #60a5fa; font-weight: bold;">🌟 {st.session_state.xp}</span>
        </div>
        <div style="width: 100%; background-color: #0f172a; border-radius: 4px; height: 8px;">
            <div style="width: {progress_val * 100}%; background-color: #3b82f6; height: 100%; border-radius: 4px;"></div>
        </div>
        <div style="text-align: right; color: #64748b; font-size: 11px; margin-top: 5px;">Seviye atlamaya: {2000 - (st.session_state.xp % 2000)} XP</div>
    </div>
""", unsafe_allow_html=True)

seviye_listesi = ["A1.1", "A1.2", "A2.1", "A2.2", "B1.1", "B1.2", "B2.1", "B2.2", "C1", "C2"]
mevcut_seviye = st.session_state.seviye if st.session_state.seviye in seviye_listesi else "A1.1"

yeni_seviye = st.sidebar.selectbox("Hedef Alt Kur (Zorluk):", seviye_listesi, index=seviye_listesi.index(mevcut_seviye))
if yeni_seviye != st.session_state.seviye:
    update_level(yeni_seviye)

st.sidebar.markdown("---")
sayfa = st.sidebar.radio("📚 ÖĞRENME MODÜLLERİ", [
    "📊 Akademi Paneli", 
    "📚 Lektionen (Kur Eğitimi)", 
    "📖 Lesen (Anlama & Çıkarım)", 
    "🎧 Hören (İşitsel Hafıza)", 
    "✍️ Schreiben (Yapısal Üretim)", 
    "🗣️ Sprechen (Akıcılık Odası)", 
    "🧠 Akıllı Hafıza (SRS Kartları)"
])

# ==========================================
# 5. MODÜL İÇERİKLERİ
# ==========================================

if sayfa == "📊 Akademi Paneli":
    st.markdown('<div class="module-header">Genel Bakış</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-subtitle">Öğrenme performansın ve bugünkü görevlerin.</div>', unsafe_allow_html=True)
    
    c.execute("SELECT COUNT(*) FROM vocabulary WHERE next_review <= ?", (bugun,))
    bekleyen_kelime = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM vocabulary")
    toplam_kelime = c.fetchone()[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: 
        st.markdown(f'<div class="dashboard-card"><div class="card-title">Mevcut Kur</div><div class="card-value" style="color:#60a5fa;">{st.session_state.seviye}</div></div>', unsafe_allow_html=True)
    with col2: 
        st.markdown(f'<div class="dashboard-card"><div class="card-title">Genel Doğruluk</div><div class="card-value" style="color:#34d399;">%{accuracy_rate:.1f}</div></div>', unsafe_allow_html=True)
    with col3: 
        st.markdown(f'<div class="dashboard-card"><div class="card-title">Öğrenilen Kelime</div><div class="card-value">{toplam_kelime}</div></div>', unsafe_allow_html=True)
    with col4: 
        st.markdown(f'<div class="dashboard-card"><div class="card-title">Bugünkü Tekrar</div><div class="card-value" style="color:{"#fbbf24" if bekleyen_kelime>0 else "#4ade80"};">{bekleyen_kelime}</div></div>', unsafe_allow_html=True)

    if st.session_state.gunun_konusu:
        st.info(f"📌 **Günün Aktif Konusu:** {st.session_state.gunun_konusu} (Sınavlar bu konuya göre üretilecek)")

# ------------------------------------------
# SAYFALI VE KAPSAMLI EĞİTİM MODÜLÜ (LEKTIONEN)
# ------------------------------------------
elif sayfa == "📚 Lektionen (Kur Eğitimi)":
    st.markdown(f'<div class="module-header">📚 Kur Eğitimi: {st.session_state.seviye}</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-subtitle">Kapsamlı ders anlatımı. Sayfaları okuyarak konuyu özümse ve kelimeleri hafızana aktar.</div>', unsafe_allow_html=True)
    
    if "ders_icerigi" not in st.session_state: 
        st.session_state.ders_icerigi = None
    if "aktif_sayfa" not in st.session_state: 
        st.session_state.aktif_sayfa = 0

    if st.button("📖 Kapsamlı Yeni Ders Hazırla", type="primary", use_container_width=True):
        with st.spinner("Alman profesör kapsamlı müfredatı ve kelimeleri hazırlıyor... (Bu işlem 10-15 saniye sürebilir)"):
            sys_prompt = "Sen Almanya'nın en iyi, en samimi dilbilgisi eğitmenisin. Konuları kitap sayfası gibi bölümlere ayırarak anlatırsın."
            user_prompt = f"""
            Öğrenci {st.session_state.seviye} seviyesinde. Bu kurda öğrenmesi gereken EN KRİTİK ve KAPSAMLI gramer konusunu seç.
            Dersi 3 sayfaya böl.
            Ayrıca bu konuyla doğrudan alakalı en önemli 3 Almanca kelimeyi listele.
            
            JSON Formatı KESİNLİKLE şu yapıda olmalı:
            {{
                "ders_adi": "Gramer Konusunun Genel Adı",
                "sayfalar": [
                    {{
                        "baslik": "Sayfa 1: Konunun Temeli",
                        "anlatim": "Konuyu samimi, akıcı, esprili ve günlük hayattan örneklerle anlattığın detaylı metin.",
                        "ornekler": [{{"de": "Almanca örnek", "tr": "Türkçe çeviri"}}]
                    }},
                    {{
                        "baslik": "Sayfa 2: İleri Kurallar ve İstisnalar",
                        "anlatim": "Konunun detayları, formülleri ve dikkat edilmesi gereken noktalar.",
                        "ornekler": [{{"de": "Almanca örnek", "tr": "Türkçe çeviri"}}]
                    }}
                ],
                "yeni_kelimeler": [
                    {{"almanca": "der Tag", "turkce": "Gün", "ornek_de": "Guten Tag!", "ornek_tr": "İyi günler!", "emoji": "🌅"}}
                ]
            }}"""
            
            data = get_json_from_llm(sys_prompt, user_prompt)
            
            if data:
                st.session_state.ders_icerigi = data
                st.session_state.aktif_sayfa = 0
                st.session_state.gunun_konusu = data.get("ders_adi", "")
                st.rerun()

    if st.session_state.ders_icerigi:
        d = st.session_state.ders_icerigi
        sayfalar = d.get("sayfalar", [])
        mevcut_s = st.session_state.aktif_sayfa
        
        if sayfalar and 0 <= mevcut_s < len(sayfalar):
            sayfa_data = sayfalar[mevcut_s]
            
            ornekler_html = "".join([f"<div style='margin-bottom:12px; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 6px;'><b style='color:#60a5fa; font-size:16px;'>🇩🇪 {orn['de']}</b><br><span style='color:#94a3b8; font-size:15px;'>🇹🇷 {orn['tr']}</span></div>" for orn in sayfa_data.get('ornekler', [])])
            
            html_icerik = f"""
<div class="lesson-box">
<div style="color:#94a3b8; font-size:13px; text-transform:uppercase; margin-bottom:5px;">{d.get('ders_adi')} - Sayfa {mevcut_s + 1}/{len(sayfalar)}</div>
<h2 style="color: #a855f7; margin-top:0; border-bottom: 2px solid rgba(168,85,247,0.3); padding-bottom:10px;">{sayfa_data.get('baslik')}</h2>
<p style="font-size: 17px; line-height: 1.8; color: #f8fafc; margin-bottom: 25px;">{sayfa_data.get('anlatim')}</p>

<h4 style="color: #34d399; margin-top: 25px;">📝 Konuyla İlgili Örnekler</h4>
<div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px;">
{ornekler_html}
</div>
</div>
"""
            st.markdown(html_icerik, unsafe_allow_html=True)
            
            # Sayfalama Butonları
            col1, col2, col3 = st.columns([1,2,1])
            
            with col1:
                if mevcut_s > 0:
                    if st.button("⬅️ Önceki Sayfa", use_container_width=True):
                        st.session_state.aktif_sayfa -= 1
                        st.rerun()
            
            with col3:
                if mevcut_s < len(sayfalar) - 1:
                    if st.button("Sonraki Sayfa ➡️", use_container_width=True, type="primary"):
                        st.session_state.aktif_sayfa += 1
                        st.rerun()
                else:
                    if st.button("✅ Dersi Bitir & Kelimeleri Hafızaya Al", use_container_width=True, type="primary"):
                        kelimeler = d.get("yeni_kelimeler", [])
                        eklenen = 0
                        for k in kelimeler:
                            try:
                                c.execute("INSERT INTO vocabulary (almanca, turkce, seviye, next_review, ornek_de, ornek_tr, last_reviewed, emoji) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                          (k.get('almanca','').strip(), k.get('turkce','').strip(), st.session_state.seviye, bugun, k.get('ornek_de',''), k.get('ornek_tr',''), bugun, k.get('emoji','💠')))
                                eklenen += 1
                            except sqlite3.IntegrityError:
                                pass
                        
                        conn.commit()
                        st.session_state.xp += 50
                        c.execute("UPDATE stats SET total_xp = ? WHERE user_id=1", (st.session_state.xp,))
                        conn.commit()
                        
                        st.success(f"Tebrikler! Dersi tamamladın, +50 XP kazandın ve bu dersle ilgili {eklenen} yeni kelime Akıllı Hafıza kartlarına eklendi! Sınavlara geçebilirsin.")

# ------------------------------------------
# HEDEFE KİLİTLİ SINAV VE PRATİK MODÜLLERİ
# ------------------------------------------
elif sayfa == "📖 Lesen (Anlama & Çıkarım)":
    st.markdown(f'<div class="module-header">📖 Lesen ({st.session_state.seviye})</div>', unsafe_allow_html=True)
    
    if st.session_state.gunun_konusu:
        st.info(f"🎯 **Test Odağı:** Şu an '{st.session_state.gunun_konusu}' kuralları test edilmektedir.")
    
    if "lesen_data" not in st.session_state: 
        st.session_state.lesen_data = None
    if "lesen_cevap_verildi" not in st.session_state: 
        st.session_state.lesen_cevap_verildi = False

    if st.button("📝 Kura Uygun Sınav Hazırla", type="primary", use_container_width=True):
        with st.spinner("Alman yazar senin için içeriği hazırlıyor..."):
            st.session_state.lesen_cevap_verildi = False
            
            sys_prompt = "Sen uzman bir dilbilimci ve Almanca içerik üreticisisin."
            user_prompt = f"""
            Gerekli format JSON:
            {{
                "baslik": "Metnin Almanca başlığı",
                "metin": "Öğrencinin seviyesine uygun 3-4 cümlelik Almanca metin.",
                "ceviri": "Metnin tam Türkçe çevirisi",
                "soru": "Metnin detaylarıyla ilgili, cümle kurmayı gerektiren Almanca bir soru.",
                "ipucu": "Soruyu cevaplarken öğrenciye yol gösterecek ufak bir Türkçe ipucu."
            }}"""
            
            data = get_json_from_llm(sys_prompt, user_prompt)
            if data:
                st.session_state.lesen_data = data
                st.rerun()

    if st.session_state.lesen_data:
        d = st.session_state.lesen_data
        
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.7); padding: 30px; border-radius: 16px; border: 1px solid #475569; margin-top: 20px;">
            <h3 style="color: #60a5fa; margin-top: 0;">{d.get('baslik', 'Lesetext')}</h3>
            <p style="font-size: 18px; line-height: 1.7; color: #f8fafc;">{d['metin']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🇹🇷 Çeviriyi Gör (Tavsiye Edilmez)"):
            st.write(d["ceviri"])
            
        st.markdown(f'<div style="margin-top: 25px; padding-left: 15px; border-left: 4px solid #fbbf24;"><h4 style="color:#fbbf24; margin-bottom:5px;">Frage (Soru):</h4><p style="font-size: 17px; margin-top:0;">{d["soru"]}</p></div>', unsafe_allow_html=True)
        st.caption(f"💡 İpucu: {d.get('ipucu', '')}")
        
        if not st.session_state.lesen_cevap_verildi:
            cevap = st.text_area("Cevabını ALMANCA yaz:")
            if st.button("👩‍🏫 Kontrol Et ve Puanla", type="primary"):
                if cevap.strip():
                    with st.spinner("Öğretmen cevabını analiz ediyor..."):
                        sys_prompt = "Sen yapıcı, detaycı ve katı bir Almanca öğretmenisin."
                        user_prompt = f"""
                        Orijinal Metin: {d['metin']}
                        Sorulan Soru: {d['soru']}
                        Öğrencinin ({st.session_state.seviye}) verdiği Almanca cevap: {cevap}
                        
                        Lütfen değerlendir. JSON Formatı:
                        {{
                            "puan": 0 ile 100 arası bir tam sayı,
                            "hata_analizi": "TÜRKÇE olarak yapılan hataların tek tek açıklaması ve nedenleri.",
                            "dogru_versiyon": "Öğrencinin kurmaya çalıştığı cümlenin anadil (Muttersprachler) seviyesindeki kusursuz ve doğal Almanca versiyonu."
                        }}"""
                        
                        sonuc = get_json_from_llm(sys_prompt, user_prompt)
                        
                        if sonuc:
                            st.session_state.lesen_cevap_verildi = True
                            st.session_state.lesen_sonuc = sonuc
                            update_performance("Lesen", sonuc.get('puan', 0))
                            st.rerun()
                else:
                    st.warning("Lütfen değerlendirme için bir cevap yazın.")
        
        if st.session_state.lesen_cevap_verildi:
            sonuc = st.session_state.lesen_sonuc
            puan = sonuc.get('puan', 0)
            
            if puan >= 80:
                css_class = "feedback-success"
            elif puan >= 50:
                css_class = "feedback-warning"
            else:
                css_class = "feedback-error"
                
            st.markdown(f"""
            <div class="{css_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom:10px; margin-bottom:15px;">
                    <h3 style="margin:0;">Değerlendirme</h3>
                    <span style="font-size:24px; font-weight:bold;">{puan}/100</span>
                </div>
                <b>👩‍🏫 Öğretmenin Analizi:</b>
                <p style="margin-top:8px; line-height:1.5;">{sonuc.get('hata_analizi')}</p>
            </div>
            
            <div class="native-speaker-box">
                <span class="native-label">Alman Biri Nasıl Söylerdi? (Muttersprachler)</span>
                <span class="native-text">{sonuc.get('dogru_versiyon')}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Yeni Bir Metin Çöz"):
                st.session_state.lesen_data = None
                st.session_state.lesen_cevap_verildi = False
                st.rerun()

elif sayfa == "🎧 Hören (İşitsel Hafıza)":
    st.markdown(f'<div class="module-header">🎧 Hören ({st.session_state.seviye})</div>', unsafe_allow_html=True)
    
    if st.session_state.gunun_konusu:
        st.info(f"🎯 **Test Odağı:** '{st.session_state.gunun_konusu}' ile ilgili bir ses duyacaksın.")
    
    if "horen_data" not in st.session_state: 
        st.session_state.horen_data = None
    if "horen_cevap_verildi" not in st.session_state: 
        st.session_state.horen_cevap_verildi = False

    zorluk = st.radio("Dinleme Zorluğu:", ["Normal", "Hızlı (Doğal Konuşma hızı simülasyonu)"], horizontal=True)

    if st.button("🎧 Yeni Ses Kaydı Hazırla", type="primary", use_container_width=True):
        with st.spinner("Ses dosyası ve bağlam oluşturuluyor..."):
            st.session_state.horen_cevap_verildi = False
            
            sys_prompt = "Sen uzman bir dil eğitimcisisin."
            user_prompt = f"""
            Dinleme testi için pratik kullanıma sahip doğal bir Almanca ifade yaz.
            JSON Formatı:
            {{
                "almanca": "Yazdığın cümle. Noktalama işaretlerine dikkat et.",
                "turkce": "Cümlenin Türkçe çevirisi",
                "baglam": "Bu cümlenin hangi ortamda veya durumda söylendiğini anlatan kısa Türkçe bilgi"
            }}"""
            
            data = get_json_from_llm(sys_prompt, user_prompt)
            if data:
                st.session_state.horen_data = data
                st.rerun()

    if st.session_state.horen_data:
        d = st.session_state.horen_data
        st.info(f"📍 **Bağlam:** {d.get('baglam', 'Bilinmiyor')}")
        
        try:
            tts = gTTS(text=d["almanca"], lang='de', slow=(zorluk == "Normal"))
            sound_fp = io.BytesIO()
            tts.write_to_fp(sound_fp)
            st.markdown('<div style="background:#1e293b; padding:20px; border-radius:12px; margin-bottom:20px; text-align:center;">', unsafe_allow_html=True)
            st.audio(sound_fp, format='audio/mp3')
            st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.error("Ses motoru şu an yanıt vermiyor.")
            
        if not st.session_state.horen_cevap_verildi:
            cevap = st.text_area("Duyduğun metni BİREBİR Almanca olarak yaz (Dikte):")
            
            if st.button("👩‍🏫 Karşılaştır", type="primary"):
                if cevap.strip():
                    with st.spinner("Analiz ediliyor..."):
                        sys_prompt = "Sen bir dinleme-yazma (dikte) asistanısın."
                        user_prompt = f"""
                        Orijinal Metin: {d['almanca']}
                        Yazılan: {cevap}
                        Öğrencinin ne kadar doğru duyup yazdığını 100 üzerinden puanla.
                        JSON Formatı: {{"puan": 0-100, "hatali_kelimeler": "Yanlış yazılan kelimeler ve nedenleri. Yoksa 'Hatasız' yaz."}}"""
                        
                        sonuc = get_json_from_llm(sys_prompt, user_prompt)
                        if sonuc:
                            st.session_state.horen_cevap_verildi = True
                            st.session_state.horen_sonuc = sonuc
                            update_performance("Hören", sonuc.get('puan', 0))
                            st.rerun()
                else:
                    st.warning("Lütfen metni yazın.")
        
        if st.session_state.horen_cevap_verildi:
            sonuc = st.session_state.horen_sonuc
            puan = sonuc.get('puan', 0)
            
            if puan >= 90: 
                st.success(f"🎉 Puan: {puan}/100 - Kusursuz kulak!")
            elif puan >= 60: 
                st.warning(f"⚠️ Puan: {puan}/100 - Anlaşılabilir ancak eksikler var.")
            else: 
                st.error(f"❌ Puan: {puan}/100 - Sesleri yakalamakta zorlanıyorsun.")
                
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 10px; margin-top: 15px; border-left: 4px solid #a855f7;">
                <b style="color:#a855f7;">Orijinal Metin:</b><br><span style="font-size:18px; color:white;">{d['almanca']}</span><br><br>
                <b style="color:#94a3b8;">Türkçesi:</b><br><span style="color:#cbd5e1;">{d['turkce']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if sonuc.get('hatali_kelimeler') and sonuc.get('hatali_kelimeler') != "Hatasız":
                st.info(f"**Hata Analizi:** {sonuc.get('hatali_kelimeler')}")
            
            if st.button("🔄 Yeni Ses Kaydı Al"):
                st.session_state.horen_data = None
                st.session_state.horen_cevap_verildi = False
                st.rerun()

elif sayfa == "✍️ Schreiben (Yapısal Üretim)":
    st.markdown(f'<div class="module-header">✍️ Schreiben ({st.session_state.seviye})</div>', unsafe_allow_html=True)
    
    if st.session_state.gunun_konusu:
        st.info(f"🎯 **Test Odağı:** Derste öğrendiğin '{st.session_state.gunun_konusu}' yapılarını kullanman istenecek.")
    
    if "schreiben_gorev_data" not in st.session_state: 
        st.session_state.schreiben_gorev_data = None
    if "schreiben_cevap_verildi" not in st.session_state: 
        st.session_state.schreiben_cevap_verildi = False

    if st.button("🎯 Yeni Görev Oluştur", type="primary", use_container_width=True):
        with st.spinner("Sana uygun senaryo belirleniyor..."):
            st.session_state.schreiben_cevap_verildi = False
            
            sys_prompt = "Sen Alman dilinde eğitim veren bir profesörsün."
            user_prompt = f"""
            Öğrenciye bir durum ver ve bu duruma uygun kısa bir Almanca metin yazmasını iste.
            JSON Formatı:
            {{
                "baslik": "Görevin kısa başlığı (Türkçe)",
                "durum": "Öğrencinin ne yazması gerektiğini anlatan net Türkçe açıklama.",
                "kullanilmasi_istenen_yapilar": "Öğrenciyi zorlamak için bu metinde kullanmasını tavsiye ettiğin kural."
            }}"""
            
            data = get_json_from_llm(sys_prompt, user_prompt)
            if data:
                st.session_state.schreiben_gorev_data = data
                st.rerun()

    if st.session_state.schreiben_gorev_data:
        d = st.session_state.schreiben_gorev_data
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)); padding: 25px; border-radius: 12px; border: 1px solid #475569; border-left: 5px solid #f43f5e;">
            <h3 style="color:#f43f5e; margin-top:0;">📋 {d.get('baslik')}</h3>
            <p style="font-size:16px; color:#f8fafc;">{d.get('durum')}</p>
            <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:6px; margin-top:15px;">
                <span style="color:#94a3b8; font-size:12px; text-transform:uppercase; font-weight:bold;">Hedef Yapılar:</span><br>
                <span style="color:#fbbf24;">{d.get('kullanilmasi_istenen_yapilar')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.schreiben_cevap_verildi:
            cevap = st.text_area("Kalem Sende. Almanca metnini oluştur:", height=150)
            
            if st.button("👩‍🏫 Metni Teslim Et", type="primary"):
                if cevap.strip():
                    with st.spinner("İnceleniyor..."):
                        sys_prompt = "Sen eleştirel bir Alman dil bilgisi profesörüsün."
                        user_prompt = f"""
                        Görev: {d.get('durum')}
                        Metin: "{cevap}"
                        JSON Formatı:
                        {{
                            "puan": 0-100 (Sentaks, gramere göre),
                            "detayli_analiz": "Metindeki yapısal hataların detaylı TÜRKÇE analizi.",
                            "muttersprachler_versiyon": "Metnin tam olarak Alman bir anadil konuşurunun yazacağı akıcı hali."
                        }}"""
                        
                        sonuc = get_json_from_llm(sys_prompt, user_prompt)
                        if sonuc:
                            st.session_state.schreiben_cevap_verildi = True
                            st.session_state.schreiben_sonuc = sonuc
                            update_performance("Schreiben", sonuc.get('puan', 0))
                            st.rerun()
                else:
                    st.warning("Lütfen metni yazın.")

        if st.session_state.schreiben_cevap_verildi:
            sonuc = st.session_state.schreiben_sonuc
            puan = sonuc.get('puan', 0)
            
            if puan >= 80:
                css_class = "feedback-success"
            elif puan >= 50:
                css_class = "feedback-warning"
            else:
                css_class = "feedback-error"
                
            st.markdown(f"""
            <div class="{css_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom:10px; margin-bottom:15px;">
                    <h3 style="margin:0;">Notun:</h3>
                    <span style="font-size:24px; font-weight:bold;">{puan}/100</span>
                </div>
                <b>🔍 Profesörün İncelemesi:</b>
                <p style="margin-top:8px; line-height:1.6;">{sonuc.get('detayli_analiz')}</p>
            </div>
            
            <div class="native-speaker-box">
                <span class="native-label">Alman Standardı (Muttersprachler Niveau)</span>
                <span style="font-size: 16px; line-height: 1.6; color:white;">{sonuc.get('muttersprachler_versiyon')}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Yeni Görev Al"):
                st.session_state.schreiben_gorev_data = None
                st.session_state.schreiben_cevap_verildi = False
                st.rerun()

elif sayfa == "🗣️ Sprechen (Akıcılık Odası)":
    st.markdown(f'<div class="module-header">🗣️ Sprechen ({st.session_state.seviye})</div>', unsafe_allow_html=True)
    
    if st.session_state.gunun_konusu:
        st.info(f"🎯 **Sohbet Odağı:** Dil partnerin seninle '{st.session_state.gunun_konusu}' üzerine konuşmaya çalışacak.")
    
    if "sp_history" not in st.session_state: 
        st.session_state.sp_history = [{"role": "ai", "de": f"Hallo! Wie geht es dir heute?", "tr": "Merhaba! Bugün nasılsın?", "correction": None}]
    
    st.markdown('<div style="height: 400px; overflow-y: auto; padding: 10px; display: flex; flex-direction: column-reverse; background-color: rgba(15, 23, 42, 0.5); border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px;">', unsafe_allow_html=True)
    
    for msg in st.session_state.sp_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="align-self: flex-end; background-color: #3b82f6; color: white; padding: 12px 18px; border-radius: 18px 18px 4px 18px; margin: 8px 0; max-width: 80%;">
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            c_html = f'<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 13px; color: #fbbf24;">💡 <b>Düzeltme:</b> {msg["correction"]}</div>' if msg.get("correction") else ''
            
            st.markdown(f"""
            <div style="align-self: flex-start; background-color: #1e293b; color: #f8fafc; padding: 15px; border-radius: 18px 18px 18px 4px; margin: 8px 0; max-width: 85%;">
                <div style="font-size: 16px; font-weight: 500;">{msg["de"]}</div>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 5px;">🇹🇷 {msg["tr"]}</div>
                {c_html}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    audio_bytes = st.audio_input("Mikrofona tıkla, konuş ve gönder:")
    if audio_bytes and client:
        with st.spinner("🎙️ İşleniyor..."):
            try:
                transcription = client.audio.transcriptions.create(
                    file=("audio.wav", audio_bytes.read()), 
                    model="whisper-large-v3", 
                    response_format="json"
                )
                user_text = transcription.text
                
                st.session_state.sp_history.insert(0, {"role": "user", "content": user_text})
                
                with st.spinner("🧠 Yanıt hazırlanıyor..."):
                    sys_prompt = "Sen arkadaş canlısı bir Alman dil partnerisin. Hataları kısaca düzelt."
                    context = "".join([f"\n{m['role']}: {m.get('de', m.get('content'))}" for m in reversed(st.session_state.sp_history[:3])])
                    
                    user_prompt = f"""
                    Sohbet Geçmişi: {context}
                    Öğrenci: {user_text}
                    JSON: {{"de": "Almanca cevabın", "tr": "Türkçe çevirisi", "correction": "Hata varsa düzelt, yoksa boş bırak"}}"""
                    
                    hoca_data = get_json_from_llm(sys_prompt, user_prompt)
                    
                    if hoca_data:
                        st.session_state.sp_history.insert(0, {"role": "ai", "de": hoca_data.get("de"), "tr": hoca_data.get("tr"), "correction": hoca_data.get("correction")})
                        c.execute("UPDATE stats SET total_xp = total_xp + 20 WHERE user_id=1")
                        conn.commit()
                        st.session_state.xp += 20
                        st.rerun()
            except Exception as e:
                st.error(f"Mikrofon hatası: {e}")

# ------------------------------------------
# SRS KARTLARI (GÖRSEL HAFIZA DESTEKLİ)
# ------------------------------------------
elif sayfa == "🧠 Akıllı Hafıza (SRS Kartları)":
    st.markdown('<div class="module-header">🧠 Görsel Akıllı Hafıza</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-subtitle">Kelimeleri görsel hafızana kazı. Dersten eklenen yeni kelimeler burada karşına çıkar.</div>', unsafe_allow_html=True)
    
    c.execute("SELECT * FROM vocabulary WHERE next_review <= ?", (bugun,))
    kelimeler = c.fetchall()
    
    if not kelimeler:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 15px; padding: 40px; text-align: center; margin-top: 30px;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏆</div>
            <h2 style="color: #34d399; margin: 0;">Muhteşem!</h2>
            <p style="color: #ecfdf5; font-size: 18px; margin-top: 10px;">Tüm kelime tekrarlarını tamamladın. Yeni kelimeler için Kur Eğitimine (Lektionen) gidebilirsin!</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("➕ Veritabanına Yeni Kelime Ekle (Manuel)"):
            with st.form("yeni_kelime_form"):
                nk_alm = st.text_input("Almanca Kelime (Artikeliyle yaz: der Tisch)")
                nk_trk = st.text_input("Türkçe Anlamı")
                nk_emoji = st.text_input("Kelimeyi Temsil Eden Emoji (Örn: 🪑)", value="💠")
                nk_sev = st.selectbox("Seviye", seviye_listesi)
                nk_orn_de = st.text_input("Almanca Örnek Cümle (Opsiyonel)")
                nk_orn_tr = st.text_input("Türkçe Örnek Çeviri (Opsiyonel)")
                
                if st.form_submit_button("Kelimeyi SRS Algoritmasına Kaydet"):
                    if nk_alm and nk_trk:
                        try:
                            c.execute("INSERT INTO vocabulary (almanca, turkce, seviye, next_review, ornek_de, ornek_tr, last_reviewed, emoji) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                      (nk_alm.strip(), nk_trk.strip(), nk_sev, bugun, nk_orn_de.strip(), nk_orn_tr.strip(), bugun, nk_emoji))
                            conn.commit()
                            st.success(f"'{nk_alm}' veritabanına eklendi. Tekrar yükle.")
                        except sqlite3.IntegrityError:
                            st.error("Bu kelime zaten sistemde kayıtlı.")
                    else:
                        st.error("Almanca kelime ve Türkçe anlamı boş bırakılamaz.")
    else:
        if "kart_yuzu" not in st.session_state: 
            st.session_state.kart_yuzu = "on"
            
        kart_verisi = kelimeler[0]
        k_id, de_kelime, tr_kelime, seviye_etiketi, ease_factor, interval = kart_verisi[0:6]
        ornek_de, ornek_tr, correct_streak = kart_verisi
        emoji = kart_verisi[11] if len(kart_verisi) > 11 else "💠"
        
        st.markdown(f'<div style="text-align:right; color:#94a3b8; margin-bottom:10px;">Bekleyen Kart: <b>{len(kelimeler)}</b> | Çarpan: <b>x{ease_factor:.1f}</b></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            if st.session_state.kart_yuzu == "on":
                st.markdown(f"""
                <div class="flashcard">
                    <div style="position:absolute; top:15px; right:20px; background:#334155; padding:4px 10px; border-radius:12px; font-size:12px; font-weight:bold;">{seviye_etiketi}</div>
                    <div style="font-size: 80px; margin-bottom: 10px; filter: drop-shadow(0px 5px 10px rgba(0,0,0,0.5));">{emoji}</div>
                    <div style="font-size: 42px; font-weight: 800; color: #60a5fa; margin-bottom: 10px;">{de_kelime}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Anlamını Hatırladım / Göster", use_container_width=True, type="primary"):
                    st.session_state.kart_yuzu = "arka"
                    st.rerun()
            else:
                st.markdown(f"""
                <div class="flashcard">
                    <div style="font-size: 60px; margin-bottom: 10px;">{emoji}</div>
                    <div style="font-size: 34px; font-weight: 800; color: #fbbf24; margin-bottom: 15px;">{tr_kelime}</div>
                    <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; width: 100%;">
                        <div style="font-size: 16px; color: #cbd5e1; font-style: italic; margin-bottom: 5px;">"{ornek_de}"</div>
                        <div style="font-size: 14px; color: #94a3b8;">{ornek_tr}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                
                if c1.button("🔴 Unuttum", use_container_width=True):
                    c.execute("UPDATE vocabulary SET interval=1, ease_factor=?, next_review=?, correct_streak=0, last_reviewed=? WHERE id=?", 
                              (max(1.3, ease_factor - 0.2), bugun + timedelta(days=1), bugun, k_id))
                    conn.commit()
                    st.session_state.kart_yuzu = "on"
                    st.rerun()
                    
                if c2.button("🟡 Zorlandım", use_container_width=True):
                    c.execute("UPDATE vocabulary SET interval=?, ease_factor=?, next_review=?, last_reviewed=? WHERE id=?", 
                              (max(2, int(interval * 1.2)), max(1.3, ease_factor - 0.1), bugun + timedelta(days=max(2, int(interval * 1.2))), bugun, k_id))
                    conn.commit()
                    st.session_state.kart_yuzu = "on"
                    st.rerun()
                    
                if c3.button("🟢 Kolaydı", use_container_width=True):
                    yeni_int = max(3, int(interval * (ease_factor + 0.1) * (1.0 + correct_streak * 0.05)))
                    c.execute("UPDATE vocabulary SET interval=?, ease_factor=?, next_review=?, correct_streak=correct_streak+1, last_reviewed=? WHERE id=?", 
                              (yeni_int, ease_factor + 0.1, bugun + timedelta(days=yeni_int), bugun, k_id))
                    
                    c.execute("UPDATE stats SET total_xp = total_xp + 5 WHERE user_id=1")
                    conn.commit()
                    st.session_state.xp += 5
                    
                    st.session_state.kart_yuzu = "on"
                    st.rerun()

conn.close()

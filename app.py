elif sayfa == "📖 Okuma (Lesen)":
    st.title("📖 Okuma Odası (Lesen)")
    st.caption("Seviyene uygun dinamik metinler ve anlama testleri.")
    
    import re # Metin parçalama için gerekli
    
    if "okuma_metni" not in st.session_state: st.session_state.okuma_metni = ""
    if "okuma_ceviri" not in st.session_state: st.session_state.okuma_ceviri = ""
    if "okuma_soru" not in st.session_state: st.session_state.okuma_soru = ""
    if "okuma_durum" not in st.session_state: st.session_state.okuma_durum = "bekliyor"

    if st.button("📝 Yeni Okuma Parçası ve Soru Getir", use_container_width=True):
        if not client: st.error("API Key gerekli!")
        else:
            with st.spinner("Eğitmen seviyene uygun bir metin hazırlıyor..."):
                prompt = f"Sen profesyonel bir Almanca öğretmenisin. Öğrenci {st.session_state.seviye} seviyesinde, dili YENİ öğreniyor. Bu seviyeye TAMAMEN uygun, sadece 2-3 cümleden oluşan çok basit bir Almanca metin yaz. Altına da metinle ilgili çok basit bir Almanca soru sor. Format TIPA TIP şu olmalı:\n\nMETİN: [Almanca metin buraya]\nÇEVİRİ: [Almanca metnin ve sorunun tam Türkçe çevirisi buraya]\nSORU: [Almanca soru buraya]"
                try:
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}], model="openai/gpt-oss-120b"
                    )
                    icerik = response.choices[0].message.content
                    
                    # Yapay zekanın cevabını parçalara ayırıyoruz
                    metin_match = re.search(r"METİN:\s*(.*?)(?=ÇEVİRİ:)", icerik, re.DOTALL)
                    ceviri_match = re.search(r"ÇEVİRİ:\s*(.*?)(?=SORU:)", icerik, re.DOTALL)
                    soru_match = re.search(r"SORU:\s*(.*)", icerik, re.DOTALL)
                    
                    st.session_state.okuma_metni = metin_match.group(1).strip() if metin_match else icerik
                    st.session_state.okuma_ceviri = ceviri_match.group(1).strip() if ceviri_match else "Çeviri bulunamadı."
                    st.session_state.okuma_soru = soru_match.group(1).strip() if soru_match else ""
                    
                    st.session_state.okuma_durum = "okuyor"
                except Exception as e:
                    st.error(f"API Hatası: {e}")

    if st.session_state.okuma_durum in ["okuyor", "cevaplandi"]:
        # Ekrana sadece Almanca Metin ve Soruyu basıyoruz
        st.markdown(f'<div class="metric-box"><h5 style="color:#f8fafc;">🇩🇪 {st.session_state.okuma_metni}</h5><br><b style="color:#fbbf24;">❓ Soru: {st.session_state.okuma_soru}</b></div>', unsafe_allow_html=True)
        
        # Gizli Çeviri Butonu (Kopya Çekmek İçin)
        with st.expander("🇹🇷 Metnin ve Sorunun Çevirisini Göster (Zorlanırsan Tıkla)"):
            st.info(st.session_state.okuma_ceviri)
        
        if st.session_state.okuma_durum == "okuyor":
            # KULLANICI ARTIK TÜRKÇE CEVAP VEREBİLİR
            cevap = st.text_input("Yukarıdaki soruya cevabını TÜRKÇE olarak yaz (Örn: 'Parkta küçük bir köpek görüyor'):")
            if st.button("Kontrol Et", type="primary"):
                if cevap:
                    with st.spinner("Öğretmen cevabını inceliyor..."):
                        kontrol_prompt = f"Öğrencinin okuduğu metin: {st.session_state.okuma_metni}\nSoru: {st.session_state.okuma_soru}\nÖğrencinin verdiği TÜRKÇE cevap: '{cevap}'.\n\nÖğrenci dili yeni öğreniyor. Bu yüzden cevabı Türkçe verdi. Anlamsal olarak metne göre doğru mu anlıyor? Eğer doğru anladıysa, yanıtının en sonuna mutlaka 'DOĞRU' kelimesini büyük harflerle yaz ve nedenini Türkçe kısaca açıkla."
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

import streamlit as st
from groq import Groq
import os
from streamlit_audio_recorder import audio_recorder
import io

# --- Sayfa Yapılandırması ---
st.set_page_config(
    page_title="Ses Diyalog Ayrıştırıcı",
    page_icon="🎙️",
    layout="wide"
)

# =============================================================================
# ANA BAŞLIK
# =============================================================================
st.title("🎙️ Ses Analizi ve Diyalog Ayrıştırma")
st.markdown("Aşağıdaki seçeneklerden birini kullanarak ses analizi yapabilirsiniz: Mikrofonunuzdan yeni bir ses kaydı oluşturun veya bilgisayarınızdan mevcut bir ses dosyasını yükleyin.")

# =============================================================================
# KENAR ÇUBUĞU (SIDEBAR)
# =============================================================================
with st.sidebar:
    st.title("Ayarlar & Bilgi")
    
    # --- GİRİŞ BİLGİLERİ KONTEYNERİ ---
    with st.container(border=True):
        st.subheader("🔑 Giriş Bilgileri")
        api_key = st.text_input(
            "Groq API Anahtarınız", 
            type="password",
            placeholder="gsk_xxxxxxxxxxxxxxxx",
            help="API anahtarınız asla saklanmaz veya paylaşılmaz. Groq hesabınızdan alabilirsiniz."
        )

    # --- ANALİZ AYARLARI KONTEYNERİ ---
    with st.container(border=True):
        st.subheader("⚙️ Analiz Ayarları")
        
        selected_model = st.selectbox(
            "Ayrıştırma Modeli",
            ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
            index=0,
            help="**70B:** En akıllı ama yavaş. **8B:** En hızlı ama daha az akıllı. **Mixtral:** Uzun metinler için iyi."
        )
        
        temperature = st.slider(
            "Model Yaratıcılığı (Temperature)",
            min_value=0.0, max_value=1.0, value=0.2, step=0.1,
            help="Diyalog ayrıştırma gibi görevler için 0.1-0.3 arası düşük değerler önerilir."
        )

    # --- ALT BİLGİ ---
    st.markdown('<div class="sidebar-footer"></div>', unsafe_allow_html=True) 
    with st.container():
         st.info("Bu uygulama **BT** tarafından geliştirilmiştir.", icon="👨‍💻")

# =============================================================================
# YENİDEN KULLANILABİLİR ANALİZ FONKSİYONU
# =============================================================================
def analyze_audio(client, audio_bytes, filename, model, temp):
    """
    Verilen ses byte'larını analiz eder, transkript oluşturur,
    konuşmacıları ayırır ve sonuçları ekranda gösterir.
    """
    try:
        with st.spinner("Aşama 1/2: Ses dosyası metne dönüştürülüyor..."):
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model="whisper-large-v3",
                response_format="text",
                prompt="Bu bir doktor ve hasta arasındaki tıbbi bir görüşmedir.",
            )
            ham_metin = transcription
        st.success("Metne dönüştürme tamamlandı!")

        with st.spinner("Aşama 2/2: Konuşmacılar ayrıştırılıyor..."):
            sistem_mesaji = (
                "Senin görevin, sana verilen bir konuşma metnini analiz etmektir. "
                "Bu metin bir doktor ve bir hasta arasındaki diyaloğu içeriyor. "
                "Metni oku ve her konuşan kişiyi 'Doktor:' veya 'Hasta:' şeklinde etiketle. "
                "Cevabını sadece ve sadece düzenlenmiş diyalog metni olarak ver. Başka hiçbir açıklama ekleme."
            )
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sistem_mesaji},
                    {"role": "user", "content": f"Aşağıdaki transkripti konuşmacılara göre ayır:\n\n{ham_metin}"}
                ],
                model=model,
                temperature=temp,
                max_tokens=4096,
            )
            ayristirilmis_metin = chat_completion.choices[0].message.content
        st.success("Diyalog ayrıştırma tamamlandı!")

        st.subheader("Analiz Sonuçları")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("Ham Metin (Whisper Çıktısı)")
            st.text_area("Oluşturulan Ham Metin:", value=ham_metin, height=500, disabled=True)
        
        with col2:
            st.success("İşlenmiş Diyalog (Llama 3 Çıktısı)")
            st.text_area("Ayrıştırılmış Diyalog:", value=ayristirilmis_metin, height=500)
            st.download_button(
                label="İşlenmiş Diyaloğu İndir (.txt)",
                data=ayristirilmis_metin.encode('utf-8'),
                file_name=f"{os.path.splitext(filename)[0]}_diyalog.txt",
                mime='text/plain'
            )

    except Exception as e:
        st.error(f"Beklenmedik bir hata oluştu: {e}", icon="❗")

# =============================================================================
# SEKMELİ YAPI
# =============================================================================
tab_analiz, tab_hakkinda = st.tabs(["📊 Analiz Aracı", "ℹ️ Hakkında"])

# --- ANALİZ SEKMESİ ---
with tab_analiz:
    col1, col2 = st.columns(2, gap="large")

    # Sütun 1: Ses Kaydı Yapma
    with col1:
        st.subheader("1. Seçenek: Ses Kaydı Oluşturun")
        
        # Değiştirin: audio_recorder kullanımı
        audio = audio_recorder()

        if audio is not None:
            st.audio(audio)
            
            # Kaydedilen ses için analiz butonu
            if st.button("Kaydı Analiz Et", use_container_width=True, type="primary"):
                if not api_key:
                    st.warning("Lütfen kenar çubuğuna Groq API anahtarınızı girin.")
                else:
                    client = Groq(api_key=api_key)
                    # Kaydedilen sesi analiz fonksiyonuna gönder
                    analyze_audio(client, audio, "kaydedilen_ses.wav", selected_model, temperature)

    # Sütun 2: Dosya Yükleme
    with col2:
        st.subheader("2. Seçenek: Dosya Yükleyin")
        uploaded_file = st.file_uploader(
            "Analiz edilecek ses dosyasını seçin",
            type=['mp3', 'mp4', 'wav', 'm4a', 'ogg'],
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            st.audio(uploaded_file.read())
            
            # Yüklenen dosya için analiz butonu
            if st.button("Dosyayı Analiz Et", use_container_width=True, type="primary"):
                if not api_key:
                    st.warning("Lütfen kenar çubuğuna Groq API anahtarınızı girin.")
                else:
                    client = Groq(api_key=api_key)
                    # Yüklenen dosyanın byte'larını analiz fonksiyonuna gönder
                    analyze_audio(client, uploaded_file.getvalue(), uploaded_file.name, selected_model, temperature)

# --- HAKKINDA SEKMESİ ---
with tab_hakkinda:
    st.header("Uygulama Hakkında")
    st.markdown("""
    Bu uygulama, iki temel yapay zeka modelinin gücünü birleştirir:

    1.  **OpenAI Whisper (Groq Üzerinde):** Yüklediğiniz ses dosyasını yüksek doğrulukla metne dönüştürür. Bu aşamada konuşmacı ayrımı yapılmaz, sadece ham bir metin elde edilir.

    2.  **Meta Llama 3 (Groq Üzerinde):** Whisper'dan elde edilen ham metni alır ve bağlamı anlayarak metni "Doktor:" ve "Hasta:" gibi etiketlerle konuşmacılara göre ayırır.

    Bu araç, özellikle tıbbi diyalogların, röportajların veya toplantı kayıtlarının deşifre edilip düzenlenmesi sürecini otomatikleştirmek için tasarlanmıştır.
    """)
    
    st.subheader("Nasıl Çalışır?")
    st.info("""
    - **Giriş:** Ses Dosyası veya Mikrofon Kaydı
    - **Aşama 1 (Whisper):** Ses → Ham Metin
    - **Aşama 2 (Llama 3):** Ham Metin → Konuşmacılara Ayrılmış Diyalog
    - **Çıkış:** Düzenlenmiş Metin Dosyası
    """)

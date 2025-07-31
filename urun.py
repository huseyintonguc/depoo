import streamlit as st
import gspread
import pandas as pd

st.set_page_config(layout="centered", page_title="Depo Giriş/Çıkış Bağlantı Testi")
st.title("Google E-Tabloları Bağlantı Testi")

# --- Google Sheets Ayarları ---
try:
    # Streamlit secrets'tan servis hesabı bilgilerini çekin
    gsheets_config = st.secrets["gsheets"]

    # gspread kütüphanesini servis hesabı bilgileriyle başlatın
    gc = gspread.service_account_from_dict(gsheets_config)

    # Google E-Tablonuzun URL'sini buraya yapıştırın.
    # Örn: "https://docs.google.com/spreadsheets/d/12345abcdefg_XYZ/edit#gid=0"
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1UnHZgOBvNf3Y0ANHCvIN4IThLTgxH6iII--3jB-ZJ4E/edit?gid=1619483236#gid=1619483236" 

    # E-Tabloyu URL ile açmaya çalışın
    spreadsheet = gc.open_by_url(spreadsheet_url)

    # Products sayfasını test etmek için açın
    products_worksheet = spreadsheet.worksheet("Products") # Ürünler sayfasının adını doğru yazın!

    st.success("🎉 Başarılı! Google E-Tablolarına ve 'Products' sayfasına bağlantı sağlandı!")
    st.write("İlk 5 ürünü çekiliyor:")

    # Test için ilk 5 satırı çekip gösterelim
    data = products_worksheet.get_all_values()
    if len(data) > 1: # Başlıklar ve en az bir veri satırı varsa
        df_test = pd.DataFrame(data[1:], columns=data[0])
        st.dataframe(df_test.head(5))
    else:
        st.info("'Products' sayfasında hiç veri yok veya sadece başlıklar var.")

except gspread.exceptions.SpreadsheetNotFound:
    st.error(f"E-Tablo bulunamadı veya erişilemiyor. URL'yi kontrol edin: {spreadsheet_url}")
    st.info("E-Tablo URL'sinin doğru olduğundan ve servis hesabınızın bu e-tabloya erişim yetkisi olduğundan emin olun.")
except gspread.exceptions.NoValidUrlKeyFound:
    st.error("E-Tablo URL'si geçersiz. Lütfen doğru bir Google E-Tablosu URL'si girin.")
except KeyError as e:
    st.error(f"Secrets'ta '{e}' anahtarı bulunamadı. `.streamlit/secrets.toml` dosyanızı kontrol edin.")
    st.info("secrets.toml dosyanızda `[gsheets]` bölümünün ve içindeki tüm anahtarların doğru olduğundan emin olun.")
except gspread.exceptions.APIError as e:
    st.error(f"Google API hatası oluştu: {e}")
    st.info("Google Cloud Console'da 'Google Sheets API' ve 'Google Drive API' etkinleştirildi mi? Servis hesabınızın bu API'lere erişim izni var mı?")
except Exception as e:
    st.error(f"Beklenmedik bir hata oluştu: {e}")
    st.info("Yukarıdaki hata mesajını inceleyerek sorunu çözmeye çalışın.")

st.markdown("---")
st.info("Bu test başarılı olursa, esas uygulama kodunuzu Google Sheets entegrasyonu ile devam ettirebiliriz.")

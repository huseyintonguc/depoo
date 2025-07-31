import streamlit as st
import pandas as pd
import datetime
import gspread # gspread kütüphanesini ekledik

# --- Google Sheets Ayarları (Globals) ---
try:
    gsheets_config = st.secrets["gsheets"]
    gc = gspread.service_account_from_dict(gsheets_config)

    # Google E-Tablonuzun URL'sini buraya yapıştırın.
    # Daha önce test ettiğiniz URL olmalı!
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1UnHZgOBvNf3Y0ANHCvIN4IThLTgxH6iII--3jB-ZJ4E/edit?gid=0#gid=0" 

    spreadsheet = gc.open_by_url(SPREADSHEET_URL)
    PRODUCTS_WORKSHEET_NAME = "Products" # E-Tablonuzdaki ürünler sayfasının adı
    WAREHOUSE_ENTRIES_WORKSHEET_NAME = "Warehouse Entries" # E-Tablonuzdaki depo giriş/çıkış sayfasının adı

except Exception as e:
    st.error(f"Google Sheets bağlantı hatası: {e}. Lütfen .streamlit/secrets.toml ve E-Tablo URL'nizi kontrol edin.")
    st.stop() # Hata durumunda uygulamayı durdur

# --- Ürün Listesini Google Sheets'ten Yükle ---
@st.cache_data(ttl=3600) # Ürünler genellikle sık değişmez, 1 saat önbellekte kalabilir
def load_products():
    try:
        worksheet = spreadsheet.worksheet(PRODUCTS_WORKSHEET_NAME)
        data = worksheet.get_all_values()
        if not data:
            st.info(f"'{PRODUCTS_WORKSHEET_NAME}' sayfasında hiç veri bulunamadı. Lütfen ürün bilgisi girin.")
            return pd.DataFrame(columns=['SKU', 'Urun Adi'])

        # İlk satırı başlık olarak kullan, diğerlerini veri olarak
        df = pd.DataFrame(data[1:], columns=data[0])

        # Gerekli sütunların varlığını kontrol et
        if 'SKU' not in df.columns or 'Urun Adi' not in df.columns:
            st.error(f"'{PRODUCTS_WORKSHEET_NAME}' sayfasında 'SKU' veya 'Urun Adi' sütunları bulunamadı. Sütun başlıklarını kontrol edin.")
            return pd.DataFrame(columns=['SKU', 'Urun Adi'])

        return df[['SKU', 'Urun Adi']] # Sadece bu sütunları al
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"'{PRODUCTS_WORKSHEET_NAME}' adlı sayfa bulunamadı. E-tablonuzdaki sayfa adını kontrol edin.")
        return pd.DataFrame(columns=['SKU', 'Urun Adi'])
    except Exception as e:
        st.error(f"Ürünler yüklenirken bir hata oluştu: {e}")
        return pd.DataFrame(columns=['SKU', 'Urun Adi'])

def save_products(df):
    try:
        worksheet = spreadsheet.worksheet(PRODUCTS_WORKSHEET_NAME)
        # Mevcut tüm veriyi sil ve yeni DataFrame'i yaz
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Ürünler Google Sheets'e kaydedilirken bir hata oluştu: {e}")
        return False

# --- Depo Giriş/Çıkışlarını Google Sheets'ten Yükle ve Kaydet ---
@st.cache_data(ttl=1) # Depo kayıtları daha sık güncellenebilir
def load_warehouse_entries():
    try:
        worksheet = spreadsheet.worksheet(WAREHOUSE_ENTRIES_WORKSHEET_NAME)
        data = worksheet.get_all_values()
        if not data:
            st.info(f"'{WAREHOUSE_ENTRIES_WORKSHEET_NAME}' sayfasında hiç veri bulunamadı. Yeni girişler beklenecek.")
            return pd.DataFrame(columns=['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi'])

        df = pd.DataFrame(data[1:], columns=data[0])

        # Gerekli sütunların varlığını kontrol et
        required_cols = ['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi']
        if not all(col in df.columns for col in required_cols):
            st.error(f"'{WAREHOUSE_ENTRIES_WORKSHEET_NAME}' sayfasında eksik sütunlar var. Gerekli sütunlar: {', '.join(required_cols)}.")
            return pd.DataFrame(columns=required_cols)

        df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date
        df['Adet'] = pd.to_numeric(df['Adet'], errors='coerce').fillna(0).astype(int)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"'{WAREHOUSE_ENTRIES_WORKSHEET_NAME}' adlı sayfa bulunamadı. E-tablonuzdaki sayfa adını kontrol edin.")
        return pd.DataFrame(columns=['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi'])
    except Exception as e:
        st.error(f"Depo giriş/çıkışları yüklenirken bir hata oluştu: {e}")
        return pd.DataFrame(columns=['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi'])

def save_warehouse_entry(entry_df):
    try:
        worksheet = spreadsheet.worksheet(WAREHOUSE_ENTRIES_WORKSHEET_NAME)
        # Mevcut tüm veriyi sil ve yeni DataFrame'i yaz
        # Tarih sütununu gspread'in anlayacağı string formatına çevir
        if 'Tarih' in entry_df.columns:
            entry_df['Tarih'] = entry_df['Tarih'].apply(lambda x: x.isoformat() if isinstance(x, (datetime.date, datetime.datetime)) else x)

        worksheet.clear()
        worksheet.update([entry_df.columns.values.tolist()] + entry_df.values.tolist())
        return True 
    except Exception as e:
        st.error(f"Depo girişi/çıkışı Google Sheets'e kaydedilirken bir hata oluştu: {e}")
        return False

# --- Uygulama Başlığı ---
st.set_page_config(layout="centered", page_title="Depo Giriş/Çıkış Kayıt Sistemi")
st.title("📦 Depo Giriş/Çıkış Kayıt Sistemi")
st.markdown("Gün içinde depoya alınan ve depodan çıkan ürünleri buraya kaydedin.")

# --- Session State Başlatma ---
if 'products_df' not in st.session_state:
    st.session_state['products_df'] = load_products()

if 'warehouse_entries_df' not in st.session_state or st.session_state['warehouse_entries_df'] is None:
    st.session_state['warehouse_entries_df'] = load_warehouse_entries()

products_df = st.session_state['products_df']
warehouse_entries_df = st.session_state['warehouse_entries_df']


# --- Yeni Ürün Ekleme Bölümü ---
st.markdown("---")
st.subheader("➕ Yeni Ürün Ekle")
new_product_sku = st.text_input("Yeni Ürün SKU'su", key="new_sku_input").strip()
new_product_name = st.text_input("Yeni Ürün Adı", key="new_product_name_input").strip()

if st.button("Yeni Ürünü Kaydet"):
    if new_product_sku and new_product_name:
        if not products_df.empty and new_product_sku in products_df['SKU'].values:
            st.warning(f"SKU '{new_product_sku}' zaten mevcut. Lütfen farklı bir SKU girin.")
        else:
            new_product_data = pd.DataFrame([{
                'SKU': new_product_sku,
                'Urun Adi': new_product_name
            }])

            if products_df.empty:
                st.session_state['products_df'] = new_product_data
            else:
                st.session_state['products_df'] = pd.concat([products_df, new_product_data], ignore_index=True)

            if save_products(st.session_state['products_df']):
                st.success(f"Yeni ürün **{new_product_name}** (SKU: **{new_product_sku}**) başarıyla eklendi!")
                load_products.clear() # Ürün önbelleğini temizle
                st.session_state['products_df'] = load_products() # Güncel veriyi yeniden yükle
                st.rerun() # Sayfayı yeniden yükle
            else:
                st.error("Yeni ürün kaydedilirken bir sorun oluştu.")
    else:
        st.warning("Lütfen hem SKU hem de Ürün Adı girin.")

st.markdown("---") # Yeni ürün ekleme alanı ile ürün arama arasına ayırıcı

# Eğer ürün listesi boşsa uyarı ver
if products_df.empty:
    st.warning("Ürün listesi boş veya yüklenemedi. Lütfen Google Sheets'teki 'Products' sayfasını kontrol edin veya yukarıdan yeni ürün ekleyin.")
else:
    # --- Ürün Arama ve Seçme ---
    st.subheader("Ürün Bilgileri")

    search_query = st.text_input("Ürün Adı veya SKU ile Ara", key="search_input_val").strip() 

    filtered_products = products_df.copy()
    if 'Urun Adi' in filtered_products.columns and 'SKU' in filtered_products.columns:
        if search_query: 
            filtered_products = products_df[
                products_df['Urun Adi'].str.contains(search_query, case=False, na=False) |
                products_df['SKU'].str.contains(search_query, case=False, na=False) 
            ]
            if filtered_products.empty:
                st.info("Aradığınız ürün bulunamadı.")
    else:
        st.warning("Ürün arama ve filtreleme yapılamıyor: 'Urun Adi' veya 'SKU' sütunları bulunamadı.")
        filtered_products = pd.DataFrame(columns=['SKU', 'Urun Adi']) 

    product_options = [f"{row['SKU']} - {row['Urun Adi']}" for index, row in filtered_products.iterrows()]

    selected_product_display = st.selectbox(
        "Ürün Seçin",
        options=['Seçiniz...'] + product_options,
        key="product_select_val" 
    )

    selected_sku = None
    selected_product_name = None

    if selected_product_display != 'Seçiniz...':
        parts = selected_product_display.split(' - ', 1) 
        selected_sku = parts[0]
        selected_product_name = parts[1] if len(parts) > 1 else "" 
        st.info(f"Seçilen Ürün: **{selected_product_name}** (SKU: **{selected_sku}**)")

    # --- İşlem Tipi ve Adet Girişi ---
    st.subheader("İşlem Detayları")

    # İşlem tipi seçimi
    transaction_type = st.radio(
        "İşlem Tipi",
        ('Giriş', 'Çıkış'),
        key="transaction_type_val"
    )

    # Adet giriş alanının metnini işlem tipine göre değiştir
    quantity_label = "Alınan Adet" if transaction_type == 'Giriş' else "Verilen Adet"

    quantity_default = st.session_state.get("quantity_input_val", 1) 
    quantity = st.number_input(quantity_label, min_value=1, value=quantity_default, step=1, key="quantity_input_val")

    # --- Tarih Seçimi (Varsayılan Bugün) ---
    entry_date = st.date_input("Tarih", value=datetime.date.today(), key="date_input_val")

    # --- Kaydet Butonu ---
    if st.button("Kaydet"):
        if selected_sku and quantity > 0:
            new_entry = pd.DataFrame([{
                'Tarih': entry_date.isoformat(), 
                'SKU': selected_sku,
                'Urun Adi': selected_product_name,
                'Adet': quantity,
                'Islem Tipi': transaction_type 
            }])

            if warehouse_entries_df.empty:
                updated_df_to_save = new_entry
            else:
                updated_df_to_save = pd.concat([warehouse_entries_df, new_entry], ignore_index=True)

            if save_warehouse_entry(updated_df_to_save): 
                st.success(f"**{quantity}** adet **{selected_product_name}** ({selected_sku}) **{entry_date.strftime('%d.%m.%Y')}** tarihinde **{transaction_type}** olarak kaydedildi!")

                load_warehouse_entries.clear() # Önbelleği temizle
                st.session_state['warehouse_entries_df'] = load_warehouse_entries() # Güncel veriyi yeniden yükle
                st.rerun() 

        else:
            st.warning("Lütfen bir ürün seçin ve geçerli bir adet girin.")

    st.markdown("---")
    st.subheader("Son Depo İşlemleri")
    if not warehouse_entries_df.empty:
        st.dataframe(warehouse_entries_df[['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi']].sort_values(by='Tarih', ascending=False).head(10))
    else:
        st.info("Henüz hiç depo işlemi yapılmadı.")

    st.markdown("---")
    st.subheader("Tüm Depo İşlemleri")
    if not warehouse_entries_df.empty:

        st.dataframe(warehouse_entries_df[['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi']], use_container_width=True)

        st.markdown("---")
        st.subheader("Kayıt Silme Alanı")

        if not warehouse_entries_df.empty:
            for i in range(len(warehouse_entries_df)):
                row = warehouse_entries_df.iloc[i]

                unique_key = f"delete_button_{i}_{row['SKU']}_{row['Tarih']}_{row['Adet']}_{row['Islem Tipi']}" 

                display_text = f"{row['Tarih'].strftime('%d.%m.%Y')} - {row['Urun Adi']} ({row['SKU']}) - {row['Adet']} {row['Islem Tipi']}"

                col_text, col_button = st.columns([0.8, 0.2])
                with col_text:
                    st.write(display_text)
                with col_button:
                    if st.button(f"Sil", key=unique_key):
                        st.session_state['warehouse_entries_df'] = st.session_state['warehouse_entries_df'].drop(row.name).reset_index(drop=True)
                        if save_warehouse_entry(st.session_state['warehouse_entries_df']):
                            st.success(f"Kayıt başarıyla silindi: {display_text}")
                            load_warehouse_entries.clear() 
                            st.session_state['warehouse_entries_df'] = load_warehouse_entries() 
                            st.rerun() 
        else:
            st.info("Silinecek bir depo işlemi bulunmamaktadır.")


        st.markdown("---") 
        df_for_download = warehouse_entries_df.copy()
        if 'Tarih' in df_for_download.columns:
            df_for_download['Tarih'] = df_for_download['Tarih'].apply(lambda x: x.isoformat() if isinstance(x, datetime.date) else x)

        st.download_button(
            label="Tüm Depo İşlemlerini İndir (CSV)",
            data=df_for_download.to_csv(index=False, encoding='utf-8').encode('utf-8'),
            file_name="tum_depo_islemleri.csv",
            mime="text/csv",
        )
    else:
        st.info("Depo işlemleri henüz boş.")

    st.markdown("---")
    st.subheader("Raporlama ve Özet")

    if not warehouse_entries_df.empty:
        # --- Tarih Aralığı Filtreleri ---
        col_start_date, col_end_date = st.columns(2)
        with col_start_date:
            start_date = st.date_input("Başlangıç Tarihi", value=warehouse_entries_df['Tarih'].min() if not warehouse_entries_df.empty else datetime.date.today(), key="report_start_date")
        with col_end_date:
            end_date = st.date_input("Bitiş Tarihi", value=warehouse_entries_df['Tarih'].max() if not warehouse_entries_df.empty else datetime.date.today(), key="report_end_date")

        # Tarih filtrelemesi yap
        filtered_by_date_df = warehouse_entries_df[
            (warehouse_entries_df['Tarih'] >= start_date) & 
            (warehouse_entries_df['Tarih'] <= end_date)
        ].copy()

        if start_date > end_date:
            st.warning("Başlangıç tarihi bitiş tarihinden sonra olamaz. Lütfen tarihleri kontrol edin.")
            filtered_by_date_df = pd.DataFrame(columns=warehouse_entries_df.columns) 

        # --- Genel Toplam Giriş/Çıkış Özeti (Tarih Filtresi Uygulanmış) ---
        st.markdown("---")
        st.subheader(f"Seçili Tarih Aralığı ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}) Özeti")

        if not filtered_by_date_df.empty:
            total_giris_filtered = filtered_by_date_df[filtered_by_date_df['Islem Tipi'] == 'Giriş']['Adet'].sum()
            total_cikis_filtered = filtered_by_date_df[filtered_by_date_df['Islem Tipi'] == 'Çıkış']['Adet'].sum()

            st.markdown(f"**Toplam Giriş:** {total_giris_filtered} adet")
            st.markdown(f"**Toplam Çıkış:** {total_cikis_filtered} adet")
            st.markdown(f"**Net Stok Değişimi:** {total_giris_filtered - total_cikis_filtered} adet")
        else:
            st.info("Seçilen tarih aralığında bir işlem bulunmamaktadır.")

        st.markdown("---")

        # --- Ürüne Göre Filtreleme ve Özet (Tarih Filtresi Uygulanmış) ---
        st.subheader("Ürüne Göre Raporlama (Seçili Tarih Aralığında)")

        products_in_filtered_range = filtered_by_date_df['SKU'].unique()
        product_filter_options_in_range = ['Tüm Ürünler'] + sorted([
            f"{row['SKU']} - {row['Urun Adi']}" 
            for index, row in products_df[products_df['SKU'].isin(products_in_filtered_range)].iterrows()
        ])

        selected_product_for_report = st.selectbox(
            "Raporlanacak Ürünü Seçin",
            options=product_filter_options_in_range,
            key="product_report_select_val"
        )

        final_filtered_df = filtered_by_date_df.copy()

        if selected_product_for_report != 'Tüm Ürünler':
            selected_sku_for_report = selected_product_for_report.split(' - ')[0]
            final_filtered_df = filtered_by_date_df[filtered_by_date_df['SKU'] == selected_sku_for_report]

            if not final_filtered_df.empty:
                product_total_giris = final_filtered_df[final_filtered_df['Islem Tipi'] == 'Giriş']['Adet'].sum()
                product_total_cikis = final_filtered_df[final_filtered_df['Islem Tipi'] == 'Çıkış']['Adet'].sum()

                st.markdown(f"**{selected_product_for_report} için Toplam Giriş:** {product_total_giris} adet")
                st.markdown(f"**{selected_product_for_report} için Toplam Çıkış:** {product_total_cikis} adet")
                st.markdown(f"**{selected_product_for_report} için Net Stok Değişimi:** {product_total_giris - product_total_cikis} adet")

                st.dataframe(final_filtered_df[['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi']].sort_values(by='Tarih', ascending=False), use_container_width=True)
            else:
                st.info(f"{selected_product_for_report} için seçilen tarih aralığında hiçbir işlem bulunamadı.")
        else:
            st.info("Seçilen tarih aralığındaki tüm ürünlerin hareketliliği aşağıdaki tabloda gösterilmektedir.")
            st.dataframe(final_filtered_df[['Tarih', 'SKU', 'Urun Adi', 'Adet', 'Islem Tipi']].sort_values(by='Tarih', ascending=False), use_container_width=True)

    else:
        st.info("Raporlama için henüz hiç depo işlemi bulunmamaktadır.")

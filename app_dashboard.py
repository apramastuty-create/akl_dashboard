import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Laporan Izin Edar", layout="wide")
st.title("📊 Laporan Monitoring Izin Edar Alkes")
st.markdown("Ringkasan status kedaluwarsa produk untuk keperluan manajemen")
st.markdown("---")

# ==========================================
# MEMBACA DAN MEMPROSES DATA
# ==========================================
# Menggunakan cache versi terbaru (@st.cache_data)
@st.cache_data
def load_data():
    # Langsung baca file bersih yang Anda miliki
    df = pd.read_excel("ijin_edar_2_PT_Urut_Expired.xlsx")
    
    # Memastikan kolom TGL EXP diproses menjadi format tanggal
    if 'TGL EXP' in df.columns:
        df['TGL EXP'] = pd.to_datetime(df['TGL EXP'], errors="coerce")
        # Menghitung sisa hari berdasarkan tanggal hari ini
        hari_ini = pd.Timestamp(datetime.now().date())
        df['Sisa Hari'] = (df['TGL EXP'] - hari_ini).dt.days
    
    # Buang data yang tidak punya tanggal dan urutkan dari yang paling mendesak
    if 'Sisa Hari' in df.columns:
        df = df.dropna(subset=['Sisa Hari'])
        df = df.sort_values(by='Sisa Hari', ascending=True)
        
    return df

df = load_data()

# ==========================================
# TAMPILAN DASHBOARD
# ==========================================
# Fungsi warna berdasarkan tingkat krisis
def beri_warna(hari):
    if hari < 0: return '#e74c3c'      # Merah (Expired)
    elif hari <= 180: return '#f39c12' # Kuning/Oranye (Kritis, <= 6 Bulan)
    else: return '#2ecc71'             # Hijau (Aman)

# Cek apakah data berhasil diload
if not df.empty and 'Sisa Hari' in df.columns:
    df['Warna'] = df['Sisa Hari'].apply(beri_warna)
    
    # 1. METRIK RINGKASAN (KPI untuk Bos)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Produk (2 PT)", len(df))
    col2.metric("Status: Expired", len(df[df['Sisa Hari'] < 0]))
    col3.metric("Status: Kritis (<= 6 Bulan)", len(df[(df['Sisa Hari'] >= 0) & (df['Sisa Hari'] <= 180)]))
    
    st.markdown("---")
    
    # Layout untuk Grafik (Kiri) dan Tabel (Kanan)
    col_chart, col_table = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Top 15 Izin Edar Paling Mendesak")
        
        # Ambil 15 data teratas saja agar visual grafik rapi
        df_top = df.head(15).copy()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Menggunakan kolom 'MERK' dan 'PENDAFTAR'
        if 'PENDAFTAR' in df_top.columns and 'MERK' in df_top.columns:
            # Potong teks agak tidak kepanjangan, lalu gabungkan dengan nama PT
            df_top['Label Grafik'] = df_top['MERK'].astype(str).str[:25] + "... (" + df_top['PENDAFTAR'].astype(str).str[:12] + ")"
            kolom_y = 'Label Grafik'
        else:
            kolom_y = 'MERK'
            
        sns.barplot(
            x='Sisa Hari', 
            y=kolom_y, 
            data=df_top, 
            palette=df_top['Warna'].tolist(),
            ax=ax
        )
        
        ax.set_xlabel('Sisa Masa Berlaku (Hari)', fontsize=10)
        ax.set_ylabel('Produk (Merk)', fontsize=10)
        ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, label='Batas Expired')
        plt.tight_layout()
        
        # Tampilkan ke Streamlit
        st.pyplot(fig)
        
    with col_table:
        st.subheader("Data Keseluruhan")
        # Format tanggal ke DD-MM-YYYY agar rapi saat dibaca bos
        df_tabel = df.copy()
        df_tabel['TGL EXP'] = df_tabel['TGL EXP'].dt.strftime("%d-%m-%Y")
        
        # Pilih kolom yang penting saja untuk ditampilkan, menggunakan 'MERK'
        kolom_penting = [col for col in ['PENDAFTAR', 'MERK', 'TGL EXP', 'Sisa Hari'] if col in df_tabel.columns]
        if not kolom_penting:
            kolom_penting = df_tabel.columns
            
        st.dataframe(df_tabel[kolom_penting], use_container_width=True, hide_index=True)
else:
    st.error("Data tidak bisa diproses. Pastikan file 'ijin_edar_2_PT_Clean.xlsx' berada di folder yang sama.")

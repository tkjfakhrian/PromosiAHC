import streamlit as st
from streamlit_option_menu import option_menu
import streamlit as st
import pandas as pd
import numpy as np
import math

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import davies_bouldin_score
from sklearn.preprocessing import StandardScaler
from functools import reduce
from pprint import pprint
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as sch
from io import BytesIO

class MainClass() :
    def __init__(self):
        self.data = Data()
        self.promosi = Promosi()
        self.dbi = DBI()

    # Fungsi judul halaman
    def judul_halaman(self):
        nama_app = "Aplikasi Promosi Perguruan Tinggi Menggunakan AHC"
        st.title(nama_app)

    # Fungsi menu sidebar
    def sidebar_menu(self):
        with st.sidebar:
            #selected = option_menu('Menu',['Upload Data','Tabel Distribusi','Simulasi'],
            selected = option_menu('Menu',['Upload Data','Rekomendasi DBI','Kelompok Promosi'],
            icons =["easel2", "graph-up", "table"],
            menu_icon="cast",
            default_index=0)
            
        if (selected == 'Upload Data'):
            self.data.menu_data()

        if (selected == 'Rekomendasi DBI'):
            self.dbi.RekomendasiDBI()

        if (selected == 'Kelompok Promosi'):
            self.promosi.kelompok_promosi()

class Data(MainClass) :
    def __init__(self):
        self.state = st.session_state.setdefault('state', {})
        if 'DataPenerimaan' not in self.state:
            self.state['DataPenerimaan'] = pd.DataFrame()

    def upload_DataPenerimaan(self):
        try:
            uploaded_file = st.file_uploader("Upload Data Penerimaan Mahasiswa", type=["xlsx"], key="penerimaan")
            if uploaded_file is not None:
                self.state['DataPenerimaan'] = pd.DataFrame()
                DataPenerimaan = pd.read_excel(uploaded_file)
                #DataPenerimaan = DataPenerimaan['Tahun'].astype(str)

                self.state['DataPenerimaan'] = DataPenerimaan
        except(KeyError, IndexError):
            st.error("Data yang diupload tidak sesuai")

    def tampil_DataPenerimaan(self) :
        if not self.state['DataPenerimaan'].empty:
            Data = self.state['DataPenerimaan']
            #Data['Tahun'] = Data['Tahun'].astype(str)
            st.dataframe(Data)

    def menu_data(self):
        self.judul_halaman()
        self.upload_DataPenerimaan()
        self.tampil_DataPenerimaan()

class DBI(Data) :
    def __init__(self) :
        self.state = st.session_state.setdefault('state', {})
        if 'DataPenerimaan' not in self.state:
            self.state['DataPenerimaan'] = pd.DataFrame()

    def RekomendasiDBI(self) :
        self.judul_halaman()
        try :
            DataPenerimaan = self.state['DataPenerimaan'] 
            results = {}
            for i in range(2,8) :
                hc = AgglomerativeClustering(n_clusters=i, linkage='ward')
                y_hc = hc.fit_predict(DataPenerimaan)
                db_index = davies_bouldin_score(DataPenerimaan,y_hc)
                results.update({i:db_index})

            #convert dictionary to DataFrame
            df = pd.DataFrame(list(results.items()), columns=['Jml_Clusters','Nilai_DBI'])

            #convert 'X' to numeric
            df['Jml_Clusters'] = pd.to_numeric(df['Jml_Clusters'])

            #Display the DataFrame
            st.markdown(
                """
                <style>
                .dataframe tbody tr th, .dataframe tbody tr td {
                    text-align: center;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.table(df)

            #Mencari Nilai Terkecil
            smallest_value = df['Nilai_DBI'].min()
            second_smallest_value = df['Nilai_DBI'].nsmallest(2).iloc[-1]

            #Mencari corresponding 'Jml_Clusters' values
            smallest_x = df[df['Nilai_DBI'] == smallest_value]['Jml_Clusters'].values[0]
            second_smallest_x = df[df['Nilai_DBI'] == second_smallest_value]['Jml_Clusters'].values[0]

            self.state['smallest_x'] = smallest_x
            self.state['second_smallest_x'] = second_smallest_x

            #Create Line Plot
            fig,ax = plt.subplots()
            ax.plot(df['Jml_Clusters'], df['Nilai_DBI'], marker='o')
            ax.set_xlabel('Jumlah Clusters')
            ax.set_ylabel('Nilai Davies-Boulding Index')
            ax.set_title('Grafik Rekomendasi DBI')

            #Highlight nilai terkecil dan nilai terkecil kedua
            ax.plot(smallest_x,smallest_value,marker='o',markersize=10,color='red',label='Jml Cluster Terbaik Ke-1')
            ax.plot(second_smallest_x,second_smallest_value,marker='o',markersize=10,color='orange',label='Jml Cluster Terbaik Ke-2')
            ax.legend()

            #display plot
            st.pyplot(fig)

            #Kesimpulan
            st.write("### Kesimpulan :")
            st.write(f"- Rekomendasi Kelompok Ke-1 Memiliki Nilai DBI : **{smallest_value:.4f}**, Sehingga Konten Promosi Dapat Dibuat Sebanyak : **{smallest_x}** Konten Promosi")
            st.write(f"- Rekomendasi Kelompok Ke-2 Memiliki Nilai DBI : **{second_smallest_value:.4f}** Sehingga Konten Promosi Dapat Dibuat Sebanyak : **{second_smallest_x}** Konten Promosi")


        except :
            st.write('Upload File Terlebih Dahulu')

class Promosi(Data) :
    def __init__(self) :
        self.state = st.session_state.setdefault('state', {})
        if 'DataPenerimaan' not in self.state:
            self.state['DataPenerimaan'] = pd.DataFrame()

        if 'smallest_x' not in self.state :
            self.state['smallest_x'] = '-'
            self.state['second_smallest_x'] = '-'
    
    def ahc_clustering(self,df,Jml_Cluster) :
        data_encoded = pd.get_dummies(df[['Sekolah', 'Provinsi', 'Fakultas', 'Prodi', 'Jalur Masuk', 'Televisi', 'Radio', 'Website', 'Facebook', 'Twitter', 'Instagram', 'Koran', 'Brosur', 'Billboard', 'Youtube', 'TikTok']]) 
        ahc = AgglomerativeClustering(n_clusters=Jml_Cluster, linkage='ward')
        labels = ahc.fit_predict(data_encoded)

        df['cluster'] = labels

        #Encode
        df['Sekolah'] = df['Sekolah'].replace([1,2,3,4,5,6,7,8],['SMA','SMK','MA','Pesantren','Home Schooling','PKBM','Konversi Univ','Paket C'])
        df['Provinsi'] = df['Provinsi'].replace([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38],['Nanggroe Aceh Darussalam (NAD)','Sumatera Utara','Sumatera Selatan','Sumatera Barat','Bengkulu','Riau','Kepulauan Riau','Jambi','Lampung','Bangka Belitung','Kalimantan Barat','Kalimantan Timur','Kalimantan Selatan','Kalimantan Tengah','Kalimantan Utara','Banten','DKI Jakarta','Jawa Barat','Jawa Tengah','DI Yogyakarta','Jawa Timur','Bali','Nusa Tenggara Timur','Nusa Tenggara Barat','Gorontalo','Sulawesi Barat','Sulawesi Tengah','Sulawesi Utara','Sulawesi Tenggara','Sulawesi Selatan','Maluku Utara','Maluku','Papua Barat','Papua','Papua Selatan','Papua Tengah','Papua Pegunungan','Papua Barat Daya'])
        df['Fakultas'] = df['Fakultas'].replace([1,2,3,4,5,6],['Teknik & Ilmu Komputer','Ekonomi dan Bisnis','Hukum','Ilmu Sosial & Ilmu Politik','Desain','Ilmu Budaya'])
        df['Prodi'] = df['Prodi'].replace([1,2,3,4,5,6,8,9,10,30,31,11,12,13,14,15,16,17,18,43,19,20,21,37,38],['Teknik Informatika - S1','Sistem Komputer - S1','Teknik Industri - S1','Teknik Arsitektur - S1','Sistem Informasi - S1','Perencanaan Wilayah dan Kota - S1','Teknik Komputer - D3','Manajemen Informatika - D3','Komputerisasi Akuntansi - D3','Teknik Sipil - S1','Teknik Elektro - S1','Akuntansi - S1','Manajemen - S1','Akuntansi - D3','Manajemen Pemasaran - D3','Keuangan dan Perbankan - D3','Ilmu Hukum - S1','Ilmu Pemerintahan - S1','Ilmu Komunikasi - S1','Hubungan Internasional - S1','Desain Komunikasi Visual - S1','Desain Interior - S1','Desain Grafis - D3','Sastra Inggris - S1','Sastra Jepang - S1'])
        df['Jalur Masuk'] = df['Jalur Masuk'].replace([1,2,3,4,5,6,7],['Prestasi','Rapor','KIP','Konversi','Peduli UNIKOM','PMDK','USM'])    

        st.dataframe(df)
    
    def to_excel(self,df) :
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='KelompokPromosi')
        writer.close()
        processed_data = output.getvalue()
        return processed_data

    def representasi_kelompok(self,df,kelompok) :
        anggota_kelas = df[df['cluster'] == kelompok]

        #Karakteristik Dari Anggota Kelas
        st.write(f"- Kelompok : **{kelompok+1}**, Memiliki Anggota Sebanyak : **{len(anggota_kelas)}**")

        #Expander Karakteristik
        with st.expander(f"Karakteristik Untuk Konten Ke-**{kelompok+1}**") :
            #list Prodi
            prodi = anggota_kelas['Prodi'].value_counts()
            prodi_list = prodi.head().index.tolist()
            prodi_str = ', '.join(prodi_list)

            # Membuat Kalimat Representasi Prodi
            st.write(f'Pada Kelompok **{kelompok+1}**, mahasiswa lebih banyak mendaftar pada prodi : **{prodi_str}**, dengan proporsi sebagai berikut :')

            #Pie Chart Proporsi Prodi
            cluster_counts = anggota_kelas['Prodi'].value_counts().head()

            #Pie Chart Prodi
            fig, ax = plt.subplots()
            ax.pie(cluster_counts, labels=cluster_counts.index, autopct='%.2f %%', startangle=90)
            ax.axis('equal') #Equal aspect ratio
            st.pyplot(fig)

            #list Provinsi
            provinsi = anggota_kelas['Provinsi'].value_counts()
            provinsi_list = provinsi.head().index.tolist()
            provinsi_str = ', '.join(provinsi_list)
            
            #List Media
            Televisi =  anggota_kelas[(anggota_kelas['Televisi'] == 1)].shape[0]
            Radio =  anggota_kelas[(anggota_kelas['Radio'] == 1)].shape[0]
            Website =  anggota_kelas[(anggota_kelas['Website'] == 1)].shape[0]
            Facebook =  anggota_kelas[(anggota_kelas['Facebook'] == 1)].shape[0]
            Twitter = anggota_kelas[(anggota_kelas['Twitter'] == 1)].shape[0]
            Instagram =  anggota_kelas[(anggota_kelas['Instagram'] == 1)].shape[0]
            Koran =  anggota_kelas[(anggota_kelas['Koran'] == 1)].shape[0]
            Brosur =  anggota_kelas[(anggota_kelas['Brosur'] == 1)].shape[0]
            Billboard =  anggota_kelas[(anggota_kelas['Billboard'] == 1)].shape[0]
            Youtube =  anggota_kelas[(anggota_kelas['Youtube'] == 1)].shape[0]
            Tiktok =  anggota_kelas[(anggota_kelas['TikTok'] == 1)].shape[0]

            media = {'Media' : ['Televisi','Radio','Website','Facebook','Twitter','Instagram','Koran','Brosur','Billboard','Youtube','TikTok'], 'Jmlh' : [Televisi,Radio,Website,Facebook,Twitter,Instagram,Koran,Brosur,Billboard,Youtube,Tiktok]}
            df_media = pd.DataFrame(media)
            df_media = df_media.sort_values(by='Jmlh', ascending=False).head()

            media_list = df_media['Media'].tolist()
            media_str =  ', '.join(media_list)

            # Membuat Kalimat Representasi Provinsi dan Media
            st.write(f'pendaftar lebih banyak berasal dari **{provinsi_str}**, mereka mengetahui UNIKOM dari : **{media_str}**')
            st.write(f'Gunakan karakteristik konten seperti ini untuk konten promosi ke-{kelompok+1}')

    def kelompok_promosi(self) :
        self.judul_halaman()
        try :
            DataPenerimaan = self.state['DataPenerimaan']
            
            st.write(f"Rekomendasi Jumlah Konten Ke-1 : **{self.state['smallest_x']}**, dan Rekomendasi Ke-2 : **{self.state['second_smallest_x']}**")
            jml_cluster = int(st.number_input('Masukkan Jumlah Konten Promosi Yang Akan Dibuat : '))
            if st.button('Buat Konten') and jml_cluster > 0:
                #Pembentukan Kelompok Menggunakan AHC Clustering
                self.ahc_clustering(DataPenerimaan,jml_cluster)
                
                #Download Ke Excel
                excel_data = self.to_excel(DataPenerimaan)
                st.download_button(label='Unduh Excel', data=excel_data, file_name='Hasil_Clustering.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

                #Representasi Pengetahuan
                for i in range(jml_cluster) :
                    self.representasi_kelompok(DataPenerimaan,i)

            else :
                st.write('Mohon Masukkan Jumlah Simulasi Terlebih Dahulu')

        except :
            st.write('Upload File Terlebih Dahulu')         

if __name__ == "__main__":
    # Create an instance of the main class
    main = MainClass()
    
main.sidebar_menu()

# streamlit_app.py
import streamlit as st
import datetime
import pandas as pd
import numpy as np
import locale

try:
    locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Indonesian_Indonesia.1252')
    except:
        print("Locale id_ID/Indonesian tidak tersedia. Format default akan digunakan.")


def format_angka(angka):
    try:
        return locale.format_string("%.0f", angka, grouping=True)
    except:
        return f"{angka:,.0f}".replace(",", ".")


try:
    from model import Problem
    from manajer_diagnosis import HardwareDiagnoser
    from konfigurasi import KATEGORI_PROBLEM, KATEGORI_DEFAULT
except ImportError as e:
    st.error(f"Gagal mengimpor modul: {e}. Pastikan file .py lain ada di direktori yang sama.")
    st.stop()

st.set_page_config(
    page_title="Diagnosis Hardware Komputer",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def get_diagnoser_manager():
    print(">>> STREAMLIT: (Cache Resource) Menginisialisasi HardwareDiagnoser...")
    return HardwareDiagnoser()


diagnoser = get_diagnoser_manager()


def halaman_tambah_masalah():
    st.header("➕ Tambah Masalah Hardware Baru")

    with st.form("form_tambah_masalah", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            nama_problem = st.text_input("Nama Masalah*", placeholder="Contoh: Komputer Lemot, No Display, WiFi Hilang")
        with col2:
            kategori = st.selectbox("Kategori*:", KATEGORI_PROBLEM, index=len(KATEGORI_PROBLEM) - 1)

        deskripsi_problem = st.text_area("Deskripsi Singkat Masalah",
                                         placeholder="Jelaskan lebih detail masalah yang terjadi...")
        penyebab = st.text_area("Penyebab Potensial*",
                                placeholder="Misalnya: RAM penuh, Driver VGA korup, Adaptor WiFi rusak")
        solusi = st.text_area("Langkah-langkah Solusi*",
                              placeholder="Misalnya: Upgrade RAM, Update/Rollback Driver, Ganti Adaptor WiFi")

        tanggal_masuk = st.date_input("Tanggal Masalah Dicatat*:", value=datetime.date.today())

        submitted = st.form_submit_button("💾 Simpan Masalah")

        if submitted:
            if not nama_problem:
                st.warning("Nama Masalah wajib diisi!", icon="⚠️")
            elif not penyebab:
                st.warning("Penyebab Potensial wajib diisi!", icon="⚠️")
            elif not solusi:
                st.warning("Langkah-langkah Solusi wajib diisi!", icon="⚠️")
            else:
                with st.spinner("Menyimpan masalah..."):
                    new_problem = Problem(
                        nama_problem=nama_problem,
                        deskripsi_problem=deskripsi_problem,
                        kategori_problem=kategori,
                        penyebab=penyebab,
                        solusi=solusi,
                        tanggal_masuk=tanggal_masuk
                    )
                    if diagnoser.tambah_problem(new_problem):
                        st.success(f"✅ OK! Masalah '{new_problem.nama_problem}' berhasil disimpan.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Gagal menyimpan masalah. Cek log atau input Anda.")


def halaman_daftar_masalah():
    st.subheader("📚 Daftar Semua Masalah Hardware")

    filter_kategori_daftar = st.selectbox(
        "Filter berdasarkan Kategori:",
        ["Semua Kategori"] + KATEGORI_PROBLEM,
        key="filter_kategori_daftar",
        on_change=st.cache_data.clear
    )

    col_date_start, col_date_end = st.columns(2)
    with col_date_start:
        date_start_filter = st.date_input(
            "Tanggal Mulai:",
            value=None,
            key="date_start_filter",
            on_change=st.cache_data.clear
        )
    with col_date_end:
        date_end_filter = st.date_input(
            "Tanggal Akhir:",
            value=None,
            key="date_end_filter",
            on_change=st.cache_data.clear
        )

    if st.button("🔄 Refresh Daftar"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Memuat daftar masalah..."):
        df_problems = diagnoser.get_dataframe_problems(
            filter_kategori=filter_kategori_daftar,
            tanggal_mulai=date_start_filter,
            tanggal_akhir=date_end_filter
        )

    if df_problems.empty:
        st.info("Belum ada masalah hardware yang dicatat.")
    else:
        df_problems_display = df_problems.copy()
        df_problems_display['Pilih'] = False

        edited_df = st.data_editor(
            df_problems_display,
            column_config={
                "ID": st.column_config.NumberColumn(
                    "ID",
                    help="ID Unik Masalah",
                    format="%d",
                    disabled=True
                ),
                "Pilih": st.column_config.CheckboxColumn(
                    "Hapus?",
                    help="Centang untuk memilih masalah ini untuk dihapus",
                    default=False,
                ),
                "Tanggal": st.column_config.DateColumn("Tanggal", format="YYYY/MM/DD", disabled=True),
                "Kategori": st.column_config.TextColumn("Kategori", disabled=True),
                "Masalah": st.column_config.TextColumn("Masalah", disabled=True),
                "Deskripsi": st.column_config.TextColumn("Deskripsi", width="medium", disabled=True),
                "Penyebab": st.column_config.TextColumn("Penyebab", width="medium", disabled=True),
                "Solusi": st.column_config.TextColumn("Solusi", width="medium", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor_problems"
        )

        # DEBUG: Cek apakah session_state.data_editor_problems ada dan memiliki edited_rows
        print(f"DEBUG APP: st.session_state.data_editor_problems: {st.session_state.get('data_editor_problems')}")
        if "data_editor_problems" in st.session_state and st.session_state.data_editor_problems.get('edited_rows'):
            edited_rows = st.session_state.data_editor_problems['edited_rows']
            print(f"DEBUG APP: edited_rows terdeteksi: {edited_rows}")

            rows_to_delete_indices = []
            for idx, changes in edited_rows.items():
                if 'Pilih' in changes and changes['Pilih'] == True:
                    rows_to_delete_indices.append(idx)

            if rows_to_delete_indices:
                print(f"DEBUG APP: Baris yang dipilih untuk dihapus (indeks): {rows_to_delete_indices}")
                st.markdown("---")
                st.subheader("🗑️ Konfirmasi Penghapusan")
                st.warning("Anda telah memilih masalah berikut untuk dihapus:", icon="⚠️")

                selected_ids = []
                for idx in rows_to_delete_indices:
                    # --- TEMPATKAN KODE KONVERSI DI SINI ---
                    problem_id_raw = df_problems.iloc[idx]['ID']

                    # Pastikan kamu sudah import numpy as np di bagian atas file
                    import numpy as np  # <-- PASTIKAN INI ADA DI ATAS FILE streamlit_app.py

                    if isinstance(problem_id_raw, (int, np.int64)):
                        problem_id = int(problem_id_raw)  # Konversi eksplisit ke int standar Python
                    elif isinstance(problem_id_raw, list) and len(problem_id_raw) > 0:
                        problem_id = int(problem_id_raw[0])  # Ambil elemen pertama jika itu list
                    else:
                        st.error(f"Error: Format ID tidak dikenali untuk baris {idx}: {problem_id_raw}")
                        continue  # Lewati baris ini jika formatnya tidak terduga
                    # --- AKHIR KODE KONVERSI ---

                    problem_name = df_problems.iloc[idx]['Masalah']
                    st.write(f"- **ID: {problem_id}** | Masalah: {problem_name}")
                    selected_ids.append(problem_id)

                print(f"DEBUG APP: ID masalah yang akan dihapus: {selected_ids}")

                if st.button("YA, Hapus Masalah yang Dipilih", key="confirm_bulk_delete"):
                        print("DEBUG APP: Tombol 'YA, Hapus Sekarang' DITEKAN!")
                        with st.spinner("Menghapus masalah yang dipilih..."):
                            all_deleted_successfully = True
                            for problem_id in selected_ids:  # Loop ini akan iterasi integer sekarang
                                print(f"DEBUG APP: Memanggil diagnoser.hapus_problem untuk ID: {problem_id}")
                                if not diagnoser.hapus_problem(problem_id):
                                    all_deleted_successfully = False
                                    st.error(f"❌ Gagal menghapus masalah dengan ID {problem_id}.")
                                    print(f"ERROR APP: Gagal menghapus ID {problem_id}. Berhenti.")
                                    break

                            if all_deleted_successfully:
                                st.success("✅ Semua masalah yang dipilih berhasil dihapus.")
                                print("DEBUG APP: Semua masalah berhasil dihapus. Membersihkan cache dan rerun.")

                            st.cache_data.clear()
                            if 'data_editor_problems' in st.session_state:
                                del st.session_state['data_editor_problems']
                            st.rerun()
                # Tombol konfirmasi TIDAK
                elif st.button("Tidak Jadi Hapus", key="cancel_bulk_delete"):
                    print("DEBUG APP: Tombol 'Tidak Jadi Hapus' DITEKAN. Membatalkan penghapusan.")
                    st.info("Penghapusan dibatalkan.")
                    if 'data_editor_problems' in st.session_state:
                        del st.session_state['data_editor_problems']
                    st.rerun()
            else:
                print("DEBUG APP: Tidak ada baris yang dipilih untuk dihapus.")
                pass
        else:
            print("DEBUG APP: Tidak ada edited_rows di data_editor_problems.")
            pass


def halaman_analisis_tren():
    st.subheader("📊 Analisis & Tren Masalah Hardware")

    st.markdown("---")
    st.markdown("#### Masalah Paling Sering Terjadi")

    col_freq_start, col_freq_end = st.columns(2)
    with col_freq_start:
        freq_date_start = st.date_input("Filter Mulai (Frekuensi):", value=None, key="freq_start_date",
                                        on_change=st.cache_data.clear)
    with col_freq_end:
        freq_date_end = st.date_input("Filter Akhir (Frekuensi):", value=None, key="freq_end_date",
                                      on_change=st.cache_data.clear)

    @st.cache_data(ttl=300)
    def get_frekuensi_cached(start_date, end_date):
        return diagnoser.get_frekuensi_problem(tanggal_mulai=start_date, tanggal_akhir=end_date)

    with st.spinner("Memuat frekuensi masalah..."):
        df_frekuensi = get_frekuensi_cached(freq_date_start, freq_date_end)

    if df_frekuensi.empty:
        st.info("Tidak ada data frekuensi masalah untuk periode ini.")
    else:
        st.dataframe(df_frekuensi, hide_index=True, use_container_width=True)
        st.bar_chart(df_frekuensi.set_index('Masalah')['Jumlah Kejadian'])

    st.markdown("---")
    st.markdown("#### Tren Masalah dari Waktu ke Waktu")

    kategori_filter_tren = st.selectbox(
        "Filter Kategori (Tren):",
        ["Semua Kategori"] + KATEGORI_PROBLEM,
        key="kategori_filter_tren",
        on_change=st.cache_data.clear
    )

    pilihan_periode_tren = st.radio(
        "Periode Tren:",
        ["Harian", "Bulanan"],
        key="periode_tren_radio",
        horizontal=True,
        on_change=st.cache_data.clear
    )

    with st.spinner(f"Memuat tren masalah {pilihan_periode_tren.lower()}..."):
        if pilihan_periode_tren == "Harian":
            @st.cache_data(ttl=300)
            def get_tren_harian_cached(kategori):
                return diagnoser.get_tren_problem_harian(kategori_problem=kategori)

            df_tren = get_tren_harian_cached(kategori_filter_tren)
        else:
            @st.cache_data(ttl=300)
            def get_tren_bulanan_cached(kategori):
                return diagnoser.get_tren_problem_bulanan(kategori_problem=kategori)

            df_tren = get_tren_bulanan_cached(kategori_filter_tren)

    if df_tren.empty:
        st.info(f"Tidak ada data tren masalah {pilihan_periode_tren.lower()} untuk kategori ini.")
    else:
        st.line_chart(df_tren['Jumlah Masalah'])


def main():
    st.sidebar.title("💻 Diagnosis Hardware Komputer")
    st.sidebar.markdown("Aplikasi Pencatat & Analisis Masalah Hardware")

    menu_pilihan = st.sidebar.radio(
        "Pilih Menu:",
        ["Tambah Masalah", "Daftar Masalah", "Analisis & Tren"],
        key="menu_utama"
    )

    st.sidebar.markdown("---")
    st.sidebar.info("Catatan kerusakan")
    st.sidebar.markdown(f"**Waktu Server:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if menu_pilihan == "Tambah Masalah":
        halaman_tambah_masalah()
    elif menu_pilihan == "Daftar Masalah":
        halaman_daftar_masalah()
    elif menu_pilihan == "Analisis & Tren":
        halaman_analisis_tren()

    st.markdown("---")
    st.caption("Pengembangan Aplikasi Berbasis OOP")


if __name__ == "__main__":
    main()
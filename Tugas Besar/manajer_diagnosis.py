# manajer_diagnosis.py

import datetime
import pandas as pd
import database
from model import Problem
from konfigurasi import KATEGORI_PROBLEM

class HardwareDiagnoser:
    _db_setup_done = False

    def __init__(self):
        """Inisialisasi awal diagnoser dan setup database jika belum dilakukan."""
        if not HardwareDiagnoser._db_setup_done:
            print("[HardwareDiagnoser] Melakukan pengecekan/setup database awal...")
            if database.setup_database_initial():
                HardwareDiagnoser._db_setup_done = True
                print("[HardwareDiagnoser] Database siap.")
            else:
                print("[HardwareDiagnoser] KRITIKAL: Setup database awal GAGAL!")
        else:
            print("[HardwareDiagnoser] Database sudah siap (skip cek awal).")

    def tambah_problem(self, problem: Problem) -> bool:
        """Menambahkan data problem baru ke database."""
        if not isinstance(problem, Problem) or not problem.nama_problem or not problem.penyebab or not problem.solusi:
            print("Peringatan: Objek Problem tidak valid atau data kunci kosong.")
            return False

        sql = """
            INSERT INTO problems 
            (nama_problem, deskripsi_problem, kategori_problem, penyebab, solusi, tanggal_masuk)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            problem.nama_problem,
            problem.deskripsi_problem,
            problem.kategori_problem,
            problem.penyebab,
            problem.solusi,
            problem.tanggal_masuk.strftime("%Y-%m-%d")
        )

        return database.execute_query(sql, params)

    def get_semua_problems(self) -> list[Problem]:
        """Mengambil semua data problem dari database dan mengembalikannya dalam bentuk list of Problem."""
        sql = """
            SELECT id, nama_problem, deskripsi_problem, kategori_problem, penyebab, solusi, tanggal_masuk 
            FROM problems 
            ORDER BY tanggal_masuk DESC, id DESC
        """
        rows = database.fetch_query(sql, fetch_all=True)
        problems_list = []

        if rows:
            for row in rows:
                problems_list.append(Problem(
                    id_problem=row['id'],
                    nama_problem=row['nama_problem'],
                    deskripsi_problem=row['deskripsi_problem'],
                    kategori_problem=row['kategori_problem'],
                    penyebab=row['penyebab'],
                    solusi=row['solusi'],
                    tanggal_masuk=row['tanggal_masuk']
                ))
        return problems_list

    def get_dataframe_problems(self, filter_kategori: str | None = None,
                               tanggal_mulai: datetime.date | None = None,
                               tanggal_akhir: datetime.date | None = None) -> pd.DataFrame:
        """Mengambil data problem dan mengembalikannya dalam bentuk DataFrame dengan filter opsional."""
        sql = """
            SELECT id, tanggal_masuk, kategori_problem, nama_problem,
                   deskripsi_problem, penyebab, solusi
            FROM problems
        """
        conditions, params = [], []

        if filter_kategori and filter_kategori != "Semua Kategori":
            conditions.append("kategori_problem = ?")
            params.append(filter_kategori)
        if tanggal_mulai:
            conditions.append("tanggal_masuk >= ?")
            params.append(tanggal_mulai.strftime("%Y-%m-%d"))
        if tanggal_akhir:
            conditions.append("tanggal_masuk <= ?")
            params.append(tanggal_akhir.strftime("%Y-%m-%d"))

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY tanggal_masuk DESC, id DESC"

        df = database.get_dataframe(sql, params=tuple(params) if params else None)
        if not df.empty:
            df = df[['id', 'tanggal_masuk', 'kategori_problem', 'nama_problem',
                     'deskripsi_problem', 'penyebab', 'solusi']]
            df.rename(columns={
                'id': 'ID',
                'tanggal_masuk': 'Tanggal',
                'kategori_problem': 'Kategori',
                'nama_problem': 'Masalah',
                'deskripsi_problem': 'Deskripsi',
                'penyebab': 'Penyebab',
                'solusi': 'Solusi'
            }, inplace=True)
        return df

    def hapus_problem(self, id_problem: int) -> bool:
        if not isinstance(id_problem, int) or id_problem <= 0: return False
        sql = "DELETE FROM problems WHERE id = ?"
        print(f"DEBUG [hapus_problem] Mencoba menghapus ID: {id_problem}")  # Tambah log ini
        return database.execute_query(sql, (id_problem,))

    def get_frekuensi_problem(self, tanggal_mulai: datetime.date = None,
                              tanggal_akhir: datetime.date = None) -> pd.DataFrame:
        """Mengembalikan frekuensi kemunculan masalah per nama_problem."""
        sql = """
            SELECT nama_problem, COUNT(id) as jumlah_kejadian
            FROM problems
        """
        conditions, params = [], []

        if tanggal_mulai:
            conditions.append("tanggal_masuk >= ?")
            params.append(tanggal_mulai.strftime("%Y-%m-%d"))
        if tanggal_akhir:
            conditions.append("tanggal_masuk <= ?")
            params.append(tanggal_akhir.strftime("%Y-%m-%d"))

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " GROUP BY nama_problem ORDER BY jumlah_kejadian DESC"

        df = database.get_dataframe(sql, params=tuple(params) if params else None)
        df.rename(columns={'nama_problem': 'Masalah', 'jumlah_kejadian': 'Jumlah Kejadian'}, inplace=True)
        return df

    def get_tren_problem_harian(self, kategori_problem: str = None) -> pd.DataFrame:
        """Mengembalikan tren jumlah masalah harian dalam bentuk DataFrame."""
        sql = """
            SELECT tanggal_masuk, COUNT(id) as jumlah_masalah
            FROM problems
        """
        conditions, params = [], []

        if kategori_problem and kategori_problem != "Semua Kategori":
            conditions.append("kategori_problem = ?")
            params.append(kategori_problem)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " GROUP BY tanggal_masuk ORDER BY tanggal_masuk ASC"

        df = database.get_dataframe(sql, params=tuple(params) if params else None)
        if not df.empty:
            df['tanggal_masuk'] = pd.to_datetime(df['tanggal_masuk'])
            df.set_index('tanggal_masuk', inplace=True)
            df = df.resample('D').sum().fillna(0)
            df.rename(columns={'jumlah_masalah': 'Jumlah Masalah'}, inplace=True)
        else:
            df = pd.DataFrame(columns=['Jumlah Masalah'])
            df.index.name = 'tanggal_masuk'

        return df

    def get_tren_problem_bulanan(self, kategori_problem: str = None) -> pd.DataFrame:
        """Mengembalikan tren jumlah masalah bulanan dalam bentuk DataFrame."""
        sql = """
            SELECT strftime('%Y-%m', tanggal_masuk) as bulan, COUNT(id) as jumlah_masalah
            FROM problems
        """
        conditions, params = [], []

        if kategori_problem and kategori_problem != "Semua Kategori":
            conditions.append("kategori_problem = ?")
            params.append(kategori_problem)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " GROUP BY bulan ORDER BY bulan ASC"

        df = database.get_dataframe(sql, params=tuple(params) if params else None)
        if not df.empty:
            df['bulan'] = pd.to_datetime(df['bulan'])
            df.set_index('bulan', inplace=True)
            df.rename(columns={'jumlah_masalah': 'Jumlah Masalah'}, inplace=True)
        else:
            df = pd.DataFrame(columns=['Jumlah Masalah'])
            df.index.name = 'bulan'

        return df

    def get_problem_by_id(self, id_problem: int) -> Problem | None:
        """Mengambil satu problem berdasarkan ID-nya."""
        sql = """
            SELECT id, nama_problem, deskripsi_problem, kategori_problem, penyebab, solusi, tanggal_masuk
            FROM problems
            WHERE id = ?
        """
        row = database.fetch_query(sql, (id_problem,), fetch_all=False)

        if row:
            return Problem(
                id_problem=row['id'],
                nama_problem=row['nama_problem'],
                deskripsi_problem=row['deskripsi_problem'],
                kategori_problem=row['kategori_problem'],
                penyebab=row['penyebab'],
                solusi=row['solusi'],
                tanggal_masuk=row['tanggal_masuk']
            )
        return None

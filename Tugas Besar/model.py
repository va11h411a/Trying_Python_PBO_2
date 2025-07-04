# model.py
import datetime

class Problem:
    def __init__(self, nama_problem: str, penyebab: str, solusi: str,
                 deskripsi_problem: str = "", kategori_problem: str = "Lainnya",
                 tanggal_masuk: datetime.date | str = None, id_problem: int | None = None):
        self.id = id_problem
        self.nama_problem = str(nama_problem) if nama_problem else "Tanpa Nama Masalah"
        self.deskripsi_problem = str(deskripsi_problem) if deskripsi_problem else ""
        self.penyebab = str(penyebab) if penyebab else "Tidak Diketahui"
        self.solusi = str(solusi) if solusi else "Tidak Ada Solusi"
        self.kategori_problem = str(kategori_problem) if kategori_problem else "Lainnya"

        if isinstance(tanggal_masuk, datetime.date): self.tanggal_masuk = tanggal_masuk
        elif isinstance(tanggal_masuk, str):
            try: self.tanggal_masuk = datetime.datetime.strptime(tanggal_masuk, "%Y-%m-%d").date()
            except ValueError: self.tanggal_masuk = datetime.date.today(); print(f"Peringatan: Format tanggal '{tanggal_masuk}' salah. Menggunakan tanggal hari ini.")
        else: self.tanggal_masuk = datetime.date.today(); print(f"Peringatan: Tipe tanggal '{type(tanggal_masuk)}' tidak valid. Menggunakan tanggal hari ini.")

    def to_dict(self) -> dict:
        return {
            "id": self.id, "nama_problem": self.nama_problem, "deskripsi_problem": self.deskripsi_problem,
            "kategori_problem": self.kategori_problem, "penyebab": self.penyebab,
            "solusi": self.solusi, "tanggal_masuk": self.tanggal_masuk.strftime("%Y-%m-%d")
        }

    def __repr__(self) -> str:
        return f"Problem(ID: {self.id}, Nama: '{self.nama_problem}', Kategori: '{self.kategori_problem}', Tanggal: {self.tanggal_masuk.strftime('%Y-%m-%d')})"
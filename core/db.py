import os, sqlite3
from datetime import datetime
from core.security import hash_password
from contextlib import closing
from typing import Optional, List, Tuple, Dict, Any

DB_PATH = os.getenv("AUTH_DB_PATH", "auth.db")
def _connect():
    # check_same_thread=False para Streamlit (varios hilos)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','user')),
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            ext TEXT NOT NULL,
            duration INTEGER,
            size_bytes INTEGER NOT NULL,
            storage_path TEXT,              -- dónde guardaste el archivo original (opcional)
            status TEXT NOT NULL,           -- pendiente | procesando | completado | error
            uploaded_at TEXT NOT NULL,
            processing_started_at TEXT,
            completed_at TEXT,
            output_path TEXT,               -- ruta del acta / texto generado
            error_message TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status);")
        conn.commit()

def seed_admin_if_empty():
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    with get_conn() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, name, email, active, created_at) VALUES (?, ?, 'admin', ?, ?, 1, ?)",
                (admin_user, hash_password(admin_pass), "Admin User", "admin@example.com", datetime.utcnow().isoformat()),
            )
            conn.commit()

def get_or_create_user(email: str, name: Optional[str] = None) -> Tuple[int, str]:
    """
    Devuelve (user_id, email). Si no existe, lo crea.
    """
    now = datetime.utcnow().isoformat()
    with closing(_connect()) as conn, conn:
        cur = conn.execute("SELECT id, email FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            return row[0], row[1]
        cur = conn.execute(
            "INSERT INTO users(email, name, created_at) VALUES(?,?,?)",
            (email, name or "", now)
        )
        return cur.lastrowid, email

def insert_document(user_id: int, filename: str, ext: str, size_bytes: int,
                    storage_path: Optional[str] = None) -> int:
    now = datetime.utcnow().isoformat()
    with closing(_connect()) as conn, conn:
        cur = conn.execute("""
            INSERT INTO documents(user_id, original_filename, ext, size_bytes, storage_path, status, uploaded_at)
            VALUES (?,?,?,?,?,'procesando',?)
        """, (user_id, filename, ext, size_bytes, storage_path, now))
        doc_id = cur.lastrowid
        conn.execute("UPDATE documents SET processing_started_at=? WHERE id=?", (now, doc_id))
        return doc_id

def update_document_status(doc_id: int, status: str,
                           output_path: Optional[str] = None,
                           duration: Optional[str] = None,
                           error_message: Optional[str] = None):
    fields = ["status=?"]
    values: List[Any] = [status]
    if output_path is not None:
        fields.append("output_path=?")
        values.append(output_path)
    if status == "completado":
        fields.append("completed_at=?")
        values.append(datetime.utcnow().isoformat())
    if duration is not None:
        fields.append("duration=?")
        values.append(duration)
    if error_message is not None:
        fields.append("error_message=?")
        values.append(error_message)
    values.append(doc_id)
    with closing(_connect()) as conn, conn:
        print(f"UPDATE documents SET {', '.join(fields)} WHERE id=?", values)
        conn.execute(f"UPDATE documents SET {', '.join(fields)} WHERE id=?", values)

def list_documents_by_user(user_id: int,
                           search: Optional[str] = None,
                           status: Optional[str] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           order_by: str = "uploaded_at DESC") -> List[Dict[str, Any]]:
    """
    date_from/date_to en formato 'YYYY-MM-DD'
    """
    clauses = ["user_id = ?"]
    params: List[Any] = [user_id]

    if search:
        clauses.append("LOWER(original_filename) LIKE ?")
        params.append(f"%{search.lower()}%")
    if status and status != "Todos":
        clauses.append("status = ?")
        params.append(status)
    if date_from:
        clauses.append("DATE(uploaded_at) >= DATE(?)")
        params.append(date_from)
    if date_to:
        clauses.append("DATE(uploaded_at) <= DATE(?)")
        params.append(date_to)

    where_sql = " AND ".join(clauses)
    sql = f"""
        SELECT id, original_filename, uploaded_at, size_bytes, status, output_path, ext, storage_path, duration
        FROM documents
        WHERE {where_sql}
        ORDER BY {order_by}
    """
    print(sql)
    with closing(_connect()) as conn:
        cur = conn.execute(sql, tuple(params))
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

def get_document(doc_id: int) -> Optional[Dict[str, Any]]:
    with closing(_connect()) as conn:
        cur = conn.execute("""
            SELECT id, user_id, original_filename, ext, size_bytes, storage_path,
                   status, uploaded_at, processing_started_at, completed_at,
                   output_path, error_message
            FROM documents WHERE id=?
        """, (doc_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

def list_all_documents(
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,   # 'YYYY-MM-DD'
    date_to: Optional[str] = None,     # 'YYYY-MM-DD'
    user_query: Optional[str] = None,  # filtrar por email o nombre
    order_by: str = "d.uploaded_at DESC",
) -> List[Dict[str, Any]]:
    clauses = ["1=1"]
    params: List[Any] = []
    if search:
        clauses.append("LOWER(d.original_filename) LIKE ?")
        params.append(f"%{search.lower()}%")
    if status and status != "Todos":
        clauses.append("d.status = ?")
        params.append(status)
    if date_from:
        clauses.append("DATE(d.uploaded_at) >= DATE(?)")
        params.append(date_from)
    if date_to:
        clauses.append("DATE(d.uploaded_at) <= DATE(?)")
        params.append(date_to)
    if user_query:
        clauses.append("(LOWER(u.email) LIKE ? OR LOWER(u.name) LIKE ?)")
        uq = f"%{user_query.lower()}%"
        params.extend([uq, uq])

    where_sql = " AND ".join(clauses)
    sql = f"""
        SELECT
            d.id, d.original_filename, d.uploaded_at, d.size_bytes, d.status, d.duration,
            d.output_path, d.storage_path, d.ext,
            u.id AS user_id, u.email, u.name
        FROM documents d
        JOIN users u ON u.id = d.user_id
        WHERE {where_sql}
        ORDER BY {order_by}
    """
    with closing(_connect()) as conn:
        cur = conn.execute(sql, tuple(params))
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

def stats_documents_by_user(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    clauses = ["1=1"]
    params: List[Any] = []
    if status and status != "Todos":
        clauses.append("d.status = ?")
        params.append(status)
    if date_from:
        clauses.append("DATE(d.uploaded_at) >= DATE(?)")
        params.append(date_from)
    if date_to:
        clauses.append("DATE(d.uploaded_at) <= DATE(?)")
        params.append(date_to)

    where_sql = " AND ".join(clauses)
    sql = f"""
        SELECT
            u.id AS user_id, u.email, u.name,
            COUNT(d.id) AS doc_count,
            COALESCE(SUM(d.duration), 0) AS total_duration,
            MAX(d.uploaded_at) AS last_upload
        FROM documents d
        JOIN users u ON u.id = d.user_id
        WHERE {where_sql}
        GROUP BY u.id, u.email, u.name
        ORDER BY doc_count DESC
    """
    with closing(_connect()) as conn:
        cur = conn.execute(sql, tuple(params))
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
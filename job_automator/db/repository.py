"""CRUD operations for all database tables."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from job_automator.db.engine import get_connection
from job_automator.db.models import Application, ColdEmail, Job, SocialPost


# --- Jobs ---

def insert_job(job: Job) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO jobs (source, title, company, location, url, description,
           salary, match_score, match_reasons, date_posted, date_discovered, raw_data)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (job.source, job.title, job.company, job.location, job.url,
         job.description, job.salary, job.match_score, job.match_reasons,
         job.date_posted, job.date_discovered, job.raw_data),
    )
    conn.commit()
    return cursor.lastrowid


def get_job(job_id: int) -> Optional[Job]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        return None
    return _row_to_job(row)


def list_jobs(
    source: Optional[str] = None,
    min_score: Optional[int] = None,
    company: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Job]:
    conn = get_connection()
    query = "SELECT * FROM jobs WHERE 1=1"
    params: list = []
    if source:
        query += " AND source = ?"
        params.append(source)
    if min_score is not None:
        query += " AND match_score >= ?"
        params.append(min_score)
    if company:
        query += " AND company LIKE ?"
        params.append(f"%{company}%")
    query += " ORDER BY match_score DESC NULLS LAST, date_discovered DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    return [_row_to_job(r) for r in rows]


def update_job_score(job_id: int, score: int, reasons: str):
    conn = get_connection()
    conn.execute(
        "UPDATE jobs SET match_score = ?, match_reasons = ? WHERE id = ?",
        (score, reasons, job_id),
    )
    conn.commit()


def job_exists_by_url(url: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM jobs WHERE url = ?", (url,)).fetchone()
    return row is not None


def count_jobs(source: Optional[str] = None) -> int:
    conn = get_connection()
    if source:
        row = conn.execute("SELECT COUNT(*) FROM jobs WHERE source = ?", (source,)).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
    return row[0]


def _row_to_job(row) -> Job:
    return Job(
        id=row["id"], source=row["source"], title=row["title"],
        company=row["company"], location=row["location"], url=row["url"],
        description=row["description"], salary=row["salary"],
        match_score=row["match_score"], match_reasons=row["match_reasons"],
        date_posted=row["date_posted"], date_discovered=row["date_discovered"],
        raw_data=row["raw_data"],
    )


# --- Applications ---

def insert_application(app: Application) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO applications (job_id, status, resume_path, cover_letter,
           notes, applied_at, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (app.job_id, app.status, app.resume_path, app.cover_letter,
         app.notes, app.applied_at, app.created_at, app.updated_at),
    )
    conn.commit()
    return cursor.lastrowid


def get_application(app_id: int) -> Optional[Application]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if not row:
        return None
    return _row_to_application(row)


def get_application_by_job(job_id: int) -> Optional[Application]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,)).fetchone()
    if not row:
        return None
    return _row_to_application(row)


def list_applications(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Application]:
    conn = get_connection()
    query = "SELECT * FROM applications WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    return [_row_to_application(r) for r in rows]


def update_application_status(app_id: int, status: str, notes: str = ""):
    conn = get_connection()
    now = datetime.now().isoformat()
    if notes:
        conn.execute(
            "UPDATE applications SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
            (status, notes, now, app_id),
        )
    else:
        conn.execute(
            "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, app_id),
        )
    conn.commit()


def update_application_materials(app_id: int, resume_path: str = "", cover_letter: str = ""):
    conn = get_connection()
    now = datetime.now().isoformat()
    updates = ["updated_at = ?"]
    params: list = [now]
    if resume_path:
        updates.append("resume_path = ?")
        params.append(resume_path)
    if cover_letter:
        updates.append("cover_letter = ?")
        params.append(cover_letter)
    params.append(app_id)
    conn.execute(f"UPDATE applications SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()


def count_applications(status: Optional[str] = None) -> int:
    conn = get_connection()
    if status:
        row = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE status = ?", (status,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) FROM applications").fetchone()
    return row[0]


def count_applications_today() -> int:
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE applied_at LIKE ?", (f"{today}%",)
    ).fetchone()
    return row[0]


def _row_to_application(row) -> Application:
    return Application(
        id=row["id"], job_id=row["job_id"], status=row["status"],
        resume_path=row["resume_path"], cover_letter=row["cover_letter"],
        notes=row["notes"], applied_at=row["applied_at"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


# --- Cold Emails ---

def insert_cold_email(email: ColdEmail) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO cold_emails (job_id, recipient_name, recipient_email,
           recipient_title, company, subject, body, status, sent_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (email.job_id, email.recipient_name, email.recipient_email,
         email.recipient_title, email.company, email.subject, email.body,
         email.status, email.sent_at, email.created_at),
    )
    conn.commit()
    return cursor.lastrowid


def get_cold_email(email_id: int) -> Optional[ColdEmail]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM cold_emails WHERE id = ?", (email_id,)).fetchone()
    if not row:
        return None
    return _row_to_cold_email(row)


def list_cold_emails(
    status: Optional[str] = None,
    limit: int = 50,
) -> list[ColdEmail]:
    conn = get_connection()
    query = "SELECT * FROM cold_emails WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    return [_row_to_cold_email(r) for r in rows]


def update_cold_email_status(email_id: int, status: str, sent_at: Optional[str] = None):
    conn = get_connection()
    if sent_at:
        conn.execute(
            "UPDATE cold_emails SET status = ?, sent_at = ? WHERE id = ?",
            (status, sent_at, email_id),
        )
    else:
        conn.execute(
            "UPDATE cold_emails SET status = ? WHERE id = ?", (status, email_id)
        )
    conn.commit()


def count_emails_sent_today() -> int:
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT COUNT(*) FROM cold_emails WHERE sent_at LIKE ?", (f"{today}%",)
    ).fetchone()
    return row[0]


def _row_to_cold_email(row) -> ColdEmail:
    return ColdEmail(
        id=row["id"], job_id=row["job_id"],
        recipient_name=row["recipient_name"], recipient_email=row["recipient_email"],
        recipient_title=row["recipient_title"], company=row["company"],
        subject=row["subject"], body=row["body"], status=row["status"],
        sent_at=row["sent_at"], created_at=row["created_at"],
    )


# --- Social Posts ---

def insert_social_post(post: SocialPost) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO social_posts (platform, post_url, author, content,
           extracted_info, job_id, discovered_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (post.platform, post.post_url, post.author, post.content,
         post.extracted_info, post.job_id, post.discovered_at),
    )
    conn.commit()
    return cursor.lastrowid


def list_social_posts(
    platform: Optional[str] = None,
    limit: int = 50,
) -> list[SocialPost]:
    conn = get_connection()
    query = "SELECT * FROM social_posts WHERE 1=1"
    params: list = []
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    query += " ORDER BY discovered_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    return [_row_to_social_post(r) for r in rows]


def social_post_exists(post_url: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM social_posts WHERE post_url = ?", (post_url,)
    ).fetchone()
    return row is not None


def _row_to_social_post(row) -> SocialPost:
    return SocialPost(
        id=row["id"], platform=row["platform"], post_url=row["post_url"],
        author=row["author"], content=row["content"],
        extracted_info=row["extracted_info"], job_id=row["job_id"],
        discovered_at=row["discovered_at"],
    )

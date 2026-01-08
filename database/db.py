import psycopg2
import dotenv
import os
import json

dotenv.load_dotenv()

def get_db_connection():
    return psycopg2.connect(os.getenv("POSTGRES_URL"))

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT UNIQUE NOT NULL,
            subscribed BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_listings (
            id SERIAL PRIMARY KEY,
            video_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            company_name TEXT,
            role TEXT,
            location TEXT,
            job_url TEXT,
            package_range TEXT,
            job_requirements TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()

def insert_job_if_not_exists(job):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO job_listings (
            video_id, title, description, company_name,
            role, location, job_url, package_range, job_requirements
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (video_id) DO NOTHING
        RETURNING id;
    """, (
        job["video_id"],
        job["title"],
        job["description"],
        job["company_name"],
        job["role"],
        job["location"],
        job["job_url"],
        job["package_range"],
        job["job_requirements"]
    ))

    result = cursor.fetchone()

    # If job already existed → fetch its ID
    if result is None:
        cursor.execute(
            "SELECT id FROM job_listings WHERE video_id = %s;",
            (job["video_id"],)
        )
        job_id = cursor.fetchone()[0]
    else:
        job_id = result[0]

    conn.commit()
    cursor.close()
    conn.close()

    return job_id

def insert_user_if_not_exists(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (chat_id, subscribed)
        VALUES (%s,%s)
        ON CONFLICT (chat_id) DO NOTHING
        RETURNING id;
    """, (chat_id, True))

    result = cursor.fetchone()

    # If user already existed → fetch its ID
    if result is None:
        cursor.execute(
            "SELECT id FROM users WHERE chat_id = %s;",
            (chat_id,)
        )
        user_id = cursor.fetchone()[0]
    else:
        user_id = result[0]

    conn.commit()
    cursor.close()
    conn.close()

    return user_id


def unsubscribe_user(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET subscribed = FALSE
        WHERE chat_id = %s;
    """, (chat_id,))

    conn.commit()
    cursor.close()
    conn.close()

def subscribe_user(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (chat_id, subscribed)
        VALUES (%s, TRUE)
        ON CONFLICT (chat_id)
        DO UPDATE SET subscribed = TRUE;
    """, (chat_id,))

    conn.commit()
    cursor.close()
    conn.close()
    
def get_subscribed_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT chat_id FROM users
        WHERE subscribed = TRUE;
    """)

    user_ids = [row[0] for row in cursor.fetchall()]

    conn.commit()
    cursor.close()
    conn.close()

    return user_ids

def check_video_exists(video_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM job_listings
        WHERE video_id = %s;
    """, (video_id,))

    exists = cursor.fetchone() is not None

    conn.commit()
    cursor.close()
    conn.close()

    return exists

def delete_first_five_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM job_listings 
        WHERE id IN (
            SELECT id FROM job_listings 
            ORDER BY created_at ASC 
            LIMIT 3
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    # initialize_db()
    delete_first_five_jobs()
    print("Database initialized and first five jobs deleted.")

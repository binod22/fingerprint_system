import psycopg2
import cv2
from processing.image_enhancement import enhance_fingerprint
from processing.feature_extraction import extract_minutiae
from processing.template_generation import generate_template
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv()
# Database connection details

DB_HOST = os.getenv("DATABASE_HOST")
DB_NAME = os.getenv("DATABASE_NAME")
DB_USER = os.getenv("DATABASE_USER")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD")

def connect_to_db():
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        print("connection established")
        print(conn)
        return conn
    except (Exception, psycopg2.Error) as error:
        print("Error connecting to database:", error)
        if conn:
          conn.close()
        return None

def store_template(conn, user_id, template):
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO fingerprint_templates (user_id, template) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET template = excluded.template", (user_id, template))
        conn.commit()
        print(f"Template stored/updated for user ID {user_id}")
    except (Exception, psycopg2.Error) as error:
        print("Error storing template:", error)
        conn.rollback()
    finally:
        cursor.close()

def load_template(conn, user_id):
    """Loads a fingerprint template from the database by user_id."""
    cursor = conn.cursor()
    template = None
    try:
        cursor.execute("SELECT template FROM fingerprint_templates WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            template = result[0]
            print(f"Template loaded for user ID {user_id}")
            print(template)
        return template
    except (Exception, psycopg2.Error) as error:
        print("Error loading template:", error)
    finally:
        cursor.close()

def main():
    # Example usage
    conn = connect_to_db()
    if not conn:
        print("Failed to connect to the database.")
        return
    # 1. Enrollment: Process and store a fingerprint template
    image_path_enroll = "./Images/fingerprint_test.jpg" 
    print("The image path is :",image_path_enroll)
    if os.path.isfile(image_path_enroll):
        try:
            print("Start working")
            print('Enhancing Process ...')
            enhanced_image = enhance_fingerprint(image_path_enroll)
            print('minutiae Extracting ...')
            minutiae = extract_minutiae(enhanced_image)
            print('template Generating ...')
            template = generate_template(minutiae)
            print('storing template ...')
            store_template(conn, 2, template) 
            #load template
            template_db = load_template(conn, 2)
        except ValueError as e:
            print(e)

    
    if conn:
        conn.close()

if __name__ == "__main__":
    main()

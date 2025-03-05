import psycopg2
import cv2
from processing.image_enhancement import enhance_fingerprint
from processing.feature_extraction import extract_minutiae
from processing.template_generation import generate_template
from matching.matcher import FingerprintMatcher
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()


DB_HOST = os.getenv("DATABASE_HOST")
DB_NAME = os.getenv("DATABASE_NAME")
DB_USER = os.getenv("DATABASE_USER")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD")


def connect_to_db():
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        print("connection established")
        return conn
    except (Exception, psycopg2.Error) as error:
        print("Error connecting to database:", error)
        if conn:
            conn.close()
        return None

def load_name(conn, code):
    cursor = conn.cursor()
    name = None
    try:
        cursor.execute("SELECT name FROM person WHERE code = %s", (code,))
        result = cursor.fetchone()
        if result:
            name = result[0]
        return name
    except (Exception, psycopg2.Error) as error:
        print("Error loading name:", error)
    finally:
        cursor.close()

def store_template(conn, code, name, template):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO person (code, name, fingerprint_template) VALUES (%s, %s, %s) ON CONFLICT (code) DO UPDATE SET fingerprint_template = excluded.fingerprint_template",
            (code, name, template))
        conn.commit()
        print(f"Template stored/updated for user with code: {code}")
    except (Exception, psycopg2.Error) as error:
        print("Error storing template:", error)
        conn.rollback()
    finally:
        cursor.close()

def verify_fingerprint(conn, image_path_verify):
    matcher = FingerprintMatcher(threshold=5)  # Adjust threshold as needed
    templates_db = load_all_templates(conn)
    if not templates_db:
        print("No templates found in the database.")
        return None
    try:
        enhanced_image = enhance_fingerprint(image_path_verify)
        minutiae = extract_minutiae(enhanced_image)
        template = generate_template(minutiae)
        print(templates_db)
        for code, template_db in templates_db:
            print(template_db)
            is_match = matcher.match_templates(template_db, template)
            if is_match:
                print(f"Fingerprint matches with code: {code}")
                return code  
        return None  
    except ValueError as e:
        print(e)
        return None
def load_template(conn, code):
    cursor = conn.cursor()
    template = None
    try:
        cursor.execute("SELECT fingerprint_template FROM person WHERE code = %s", (code,))
        result = cursor.fetchone()
        if result:
            template = result[0]
            print(f"Template loaded for user with code: {code}")
            print(template)
        return template
    except (Exception, psycopg2.Error) as error:
        print("Error loading template:", error)
    finally:
        cursor.close()

def load_all_templates(conn):
    """Loads all fingerprint templates from the database."""
    cursor = conn.cursor()
    templates = []
    try:
        cursor.execute("SELECT code, fingerprint_template FROM person")
        results = cursor.fetchall()
        for result in results:
            templates.append((result[0], result[1]))  # (code, template)
        print(f"{len(templates)} templates found in the database")
        return templates
    except (Exception, psycopg2.Error) as error:
        print("Error loading templates:", error)
        return []
    finally:
        cursor.close()
    
def delete_template(conn, code):
    """Deletes a fingerprint template from the database."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM person WHERE code = %s", (code,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Template for user with code {code} deleted successfully.")
        else:
            print(f"No template found for user with code {code}.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting template for user with code {code}:", error)
        conn.rollback()
    finally:
        cursor.close()

def main():
    conn = connect_to_db()
    if not conn:
        print("Failed to connect to the database.")
        return
    while True:
        print("\nOptions:")
        print("1. Enroll new user")
        print("2. Load template")
        print("3. Verify fingerprint")
        print("4. Delete template")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            code = input("Enter unique code for new user: ")
            name = input("Enter name of the user: ")
            print(name)
            image_path_enroll = input("Enter path to fingerprint image: ")
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
                    store_template(conn, code, name, template)
                except ValueError as e:
                    print(e)
            else:
              print("The image path does not exist")
        elif choice == '2':
            code = input("Enter user code to load template: ")
            load_template(conn, code)
        elif choice == '3':
            image_path_verify = input("Enter path to fingerprint image to verify: ")
            if os.path.isfile(image_path_verify):
                matching_code = verify_fingerprint(conn, image_path_verify)
                if matching_code:
                    name = load_name(conn,matching_code)
                    if name:
                        print(f"The person matching is : {name}")
                    
                else:
                    print("No match found.")
            else:
                print("The image path does not exist")
        elif choice == '4':
            code = input("Enter user code to delete template: ")
            delete_template(conn, code)
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")
        

    if conn:
        conn.close()


if __name__ == "__main__":
    main()

import csv
import os
import mysql.connector

def find_media_usage(db_config, media_csv_path, wp_table_name, output_csv_path):
    # Connect to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Prepare output
    usage_records = []

    # Read media URLs from CSV
    with open(media_csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            media_url = row['URL']
            filename = os.path.basename(media_url)

            # Search for filename in post_content
            query = f"""
                SELECT ID, post_title, post_type
                FROM {wp_table_name}
                WHERE post_type IN ('post', 'page')
                  AND post_status = 'publish'
                  AND post_content LIKE %s
            """
            cursor.execute(query, (f"%{filename}%",))
            results = cursor.fetchall()

            for result in results:
                usage_records.append({
                    'media_filename': filename,
                    'media_url': media_url,
                    'used_in_post_id': result['ID'],
                    'used_in_title': result['post_title'],
                    'used_in_type': result['post_type']
                })

    # Write results to CSV
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['media_filename', 'media_url', 'used_in_post_id', 'used_in_title', 'used_in_type']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(usage_records)

    print(f"Finished. Found {len(usage_records)} media usage entries written to {output_csv_path}.")
    cursor.close()
    conn.close()
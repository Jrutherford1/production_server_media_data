import csv
import os
import mysql.connector
from urllib.parse import urlparse


def fetch_media_data_per_site(db_config, site_urls_csv, output_dir_name):
    # Accepted image MIME types
    image_mime_types = {
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/jpg',
        'image/webp',
        'image/bmp',
        'image/tiff',
        'image/svg+xml'
    }

    # Helper function to execute SELECT queries
    def execute_query(cursor, query, params=None):
        cursor.execute(query, params or ())
        return cursor.fetchall()

    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Ensure the output directories exist
        data_folder = os.path.dirname(site_urls_csv)
        output_dir = os.path.join(data_folder, output_dir_name)
        os.makedirs(output_dir, exist_ok=True)

        # Read site_urls.csv
        with open(site_urls_csv, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            sites = list(reader)

        # Prepare summary data
        summary_csv = os.path.join(data_folder, 'site_media_library_summary.csv')
        summary_data = []
        total_missing_alt_text = 0
        total_image_files = 0
        total_all_media = 0

        for site in sites:
            blog_id = site['blog_id']
            site_url = site['url']

            # Extract the site name from the URL path (e.g., "slc" from "http://localhost/slc")
            parsed_url = urlparse(site_url)
            site_name = parsed_url.path.strip('/').replace('/', '_')  # Remove slashes and sanitize

            if not site_name:  # Fallback if no valid path is found
                site_name = f"site_{blog_id}"

            print(f"Processing site {blog_id} ({site_url}) as {site_name}...")

            # Table names (dynamic based on the blog_id)
            posts_table = f"scroll_{blog_id}_posts"
            postmeta_table = f"scroll_{blog_id}_postmeta"

            # Count all media files
            all_media_query = f"""
                SELECT COUNT(*) AS count
                FROM {posts_table}
                WHERE post_type = 'attachment'
            """

            # Count all image files
            all_images_query = f"""
                SELECT COUNT(*) AS count
                FROM {posts_table}
                WHERE post_type = 'attachment'
                  AND post_mime_type IN ({','.join(['%s'] * len(image_mime_types))})
            """

            # SQL: Fetch media data for images without alt text
            missing_alt_query = f"""
                SELECT
                    p.post_title AS FileTitle,
                    p.post_author AS AuthorID,
                    p.post_mime_type AS FileType,
                    p.post_date AS Date,
                    p.guid AS URL,
                    p.post_parent AS UploadedTo,
                    MAX(CASE WHEN pm.meta_key = '_wp_attachment_image_alt' THEN pm.meta_value END) AS AltText,
                    MAX(CASE WHEN pm.meta_key = '_wp_attachment_metadata' THEN pm.meta_value END) AS Description,
                    MAX(CASE WHEN pm.meta_key = '_wp_attachment_caption' THEN pm.meta_value END) AS Caption
                FROM {posts_table} p
                LEFT JOIN {postmeta_table} pm ON p.ID = pm.post_id
                WHERE p.post_type = 'attachment'
                  AND p.post_mime_type IN ({','.join(['%s'] * len(image_mime_types))})
                GROUP BY p.ID
                HAVING AltText IS NULL OR TRIM(AltText) = ''
            """

            try:
                # Get count of all media files
                all_media_result = execute_query(cursor, all_media_query)
                all_media_count = all_media_result[0]['count'] if all_media_result else 0

                # Get count of all image files
                all_images_result = execute_query(cursor, all_images_query, params=list(image_mime_types))
                all_images_count = all_images_result[0]['count'] if all_images_result else 0

                # Get images missing alt text and count
                media_data = execute_query(cursor, missing_alt_query, params=list(image_mime_types))
                missing_alt_count = len(media_data)

                # Update totals
                total_missing_alt_text += missing_alt_count
                total_image_files += all_images_count
                total_all_media += all_media_count

                # Write detailed CSV for images missing alt text
                if media_data:
                    output_csv = os.path.join(output_dir, f"{site_name}_media_{blog_id}.csv")
                    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = [
                            'FileTitle',
                            'AuthorID',
                            'FileType',
                            'Date',
                            'URL',
                            'UploadedTo',
                            'AltText',
                            'Caption',
                            'Description'
                        ]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                        # Write header
                        writer.writeheader()

                        # Write rows
                        for row in media_data:
                            writer.writerow(row)

                    print(f"Successfully wrote media data for site {blog_id} to {output_csv}.")

                # Append to summary
                summary_data.append({
                    'Site Name': site_name,
                    'Images Without Alt Text': missing_alt_count,
                    'Total Image Files': all_images_count,
                    'All Media Files': all_media_count
                })

            except mysql.connector.Error as e:
                print(f"Error querying data for site {blog_id}: {e}")
            except Exception as e:
                print(f"Error writing CSV for site {blog_id}: {e}")

        # Write summary CSV
        with open(summary_csv, mode='w', newline='', encoding='utf-8') as summary_file:
            fieldnames = ['Site Name', 'Images Without Alt Text', 'Total Image Files', 'All Media Files']
            writer = csv.DictWriter(summary_file, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Sort the summary data alphabetically by 'Site Name'
            summary_data = sorted(summary_data, key=lambda x: x['Site Name'])

            # Write site data
            for site_summary in summary_data:
                writer.writerow(site_summary)

            # Write total
            writer.writerow({
                'Site Name': 'TOTAL',
                'Images Without Alt Text': total_missing_alt_text,
                'Total Image Files': total_image_files,
                'All Media Files': total_all_media
            })

        print(f"Summary written to {summary_csv}")
        print(f"Total images without alt text: {total_missing_alt_text}")
        print(f"Total image files: {total_image_files}")
        print(f"Total all media files: {total_all_media}")

    except mysql.connector.Error as e:
        print(f"Error connecting to the database: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


# Docker database connection info
db_config = {
    'user': 'wordpress',  # Use the value from WORDPRESS_DB_USER
    'password': 'wordpress',  # Use the value from WORDPRESS_DB_PASSWORD
    'host': 'localhost',  # Accessible on localhost for services running outside Docker
    'database': 'wordpress',  # Use the value from WORDPRESS_DB_NAME
    'port': 3306,  # Database is exposed on port 3306
}

# Input file with site URLs
site_urls_csv = 'data/site_urls.csv'

# Output folder name for media data CSV files
output_dir_name = 'prod_site_media_csv_output'

# Only run if executed as a script, not when imported
if __name__ == "__main__":
    # Fetch media data and write CSVs
    fetch_media_data_per_site(db_config, site_urls_csv, output_dir_name)
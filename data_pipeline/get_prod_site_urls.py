import csv
import os
import mysql.connector

def fetch_multisite_or_primary_site_urls(db_config, output_csv_file):
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Check if the blogs table (multisite) exists
        cursor.execute("SHOW TABLES LIKE 'scroll_blogs'")
        blogs_table_exists = cursor.fetchone()

        # Retrieve URLs
        urls = []
        if blogs_table_exists:
            # Multisite: Fetch URLs from scroll_blogs table
            cursor.execute("SELECT blog_id, domain, path FROM scroll_blogs")
            sites = cursor.fetchall()

            for site in sites:
                url = f"https://{site['domain']}{site['path']}".rstrip('/')
                urls.append({'blog_id': site['blog_id'], 'url': url})

        else:
            # Single-site: Fetch primary site URL from scroll_options
            cursor.execute("SELECT option_value FROM scroll_options WHERE option_name = 'siteurl'")
            result = cursor.fetchone()
            if result:
                urls.append({'blog_id': 1, 'url': result['option_value']})

        # Ensure output directory exists
        output_dir = os.path.dirname(output_csv_file)
        if output_dir != "" and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write all URLs to a single CSV file
        with open(output_csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['blog_id', 'url'])
            writer.writeheader()
            writer.writerows(urls)

        # Print success message once
        print(f"Successfully wrote {len(urls)} site URLs to {output_csv_file}.")
    except mysql.connector.Error as e:
        print(f"Error connecting to the database: {e}")
    except Exception as e:
        print(f"Error: {e}")
        raise  # Re-raise the exception for debugging if needed
    finally:
        # Cleanup database connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
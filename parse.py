import os
import sys

# We need a special library to handle PDF files safely.
# If you don't have it, open Terminal and run: pip install pypdf
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Error: The 'pypdf' library is required to handle PDF files.")
    print("Please install it by running this command in your Terminal:")
    print("pip install pypdf")
    sys.exit(1)

def split_pdf_by_pages(input_file_path, output_dir, pages_per_file=1000):
    """
    Splits a large PDF file into smaller PDF files with a specified number of pages each.

    Args:
        input_file_path (str): The full path to the large input PDF file.
        output_dir (str): The path to the directory where smaller PDFs will be saved.
        pages_per_file (int): The number of pages to include in each smaller PDF.
    """
    
    # --- 1. Input Validation and Setup ---
    if not os.path.isfile(input_file_path):
        print(f"Error: The file '{input_file_path}' was not found.")
        return

    if not input_file_path.lower().endswith('.pdf'):
        print(f"Error: This script is designed for PDF files only. Please provide a .pdf file.")
        return

    if not os.path.isdir(output_dir):
        print(f"Output directory '{output_dir}' not found. Creating it now.")
        try:
            os.makedirs(output_dir)
        except OSError as e:
            print(f"Error creating directory '{output_dir}': {e}")
            return
            
    print(f"Starting to split '{os.path.basename(input_file_path)}'...")
    print(f"Each output PDF will contain up to {pages_per_file} pages.")

    # --- 2. PDF Splitting Logic ---
    try:
        # Open the source PDF file for reading in binary mode ('rb').
        with open(input_file_path, 'rb') as input_pdf_file:
            pdf_reader = PdfReader(input_pdf_file)
            total_pages = len(pdf_reader.pages)
            print(f"The source PDF has {total_pages} pages.")

            # Loop through the pages in chunks of 'pages_per_file'.
            for start_page in range(0, total_pages, pages_per_file):
                pdf_writer = PdfWriter()
                
                # Determine the end page for the current chunk.
                end_page = min(start_page + pages_per_file, total_pages)
                
                # Add the pages from the source PDF to our new PDF writer.
                for page_num in range(start_page, end_page):
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)

                # --- 3. Save the New PDF Chunk ---
                # Create a clear and descriptive file name.
                # Note: Page numbers are 0-indexed, so we add 1 for human-readable names.
                output_filename = f"parsed_chunk_pages_{start_page + 1}_to_{end_page}.pdf"
                output_file_path = os.path.join(output_dir, output_filename)

                # Write the new PDF to a file in binary write mode ('wb').
                with open(output_file_path, 'wb') as output_pdf_file:
                    pdf_writer.write(output_pdf_file)
                
                print(f"Creating file: {output_filename}")

        print("\n-----------------------------------------")
        print("✅ PDF splitting completed successfully!")
        print(f"   Total pages processed: {total_pages}")
        print(f"   Output files are located in: '{output_dir}'")
        print("-----------------------------------------")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check that the input is a valid, uncorrupted PDF file.")


# --- How to Run This Script ---
if __name__ == "__main__":
    """
    This is the main entry point of the script.
    To use it:
    1. Make sure you have the 'pypdf' library installed.
       - In Terminal, run: pip install pypdf
    2. Save this code as a Python file (e.g., `pdf_splitter.py`).
    3. Open the Terminal application on your Mac.
    4. Navigate to the directory where you saved the file.
       - Example: cd ~/Documents
    5. Run the script using the python3 command.
       - Example: python3 pdf_splitter.py
    6. The script will then ask you for the required file paths.
    """
    
    print("--- Large PDF File Splitter ---")
    
    # Get the path to the large file from the user.
    # You can drag and drop the file onto the Terminal window to get its full path.
    input_path = input("➡️  Enter the full path to the large PDF you want to split: ").strip()
    
    # Get the path for the output directory.
    output_path = input("➡️  Enter the path to the folder where you want to save the smaller PDFs: ").strip()

    # Call the main function to start the process.
    split_pdf_by_pages(input_path, output_path)
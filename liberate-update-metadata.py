# alter audiobooks in metadata
import os
import csv
import shutil
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TMED, TCMP
from pathlib import Path
import re

def clean_string(s):
    """Clean string for comparison by removing special chars and converting to lowercase"""
    if not s:
        return ""
    # Remove special characters and convert to lowercase
    cleaned = re.sub(r'[^\w\s]', '', s.lower())
    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned

def find_matching_audiobook(filepath, audiobooks):
    """
    Try multiple matching strategies to find the correct audiobook
    Returns the matching key or None
    """
    filename = os.path.basename(filepath)
    parent_dir = os.path.basename(os.path.dirname(filepath))
    
    # Clean the filepath components
    clean_filename = clean_string(filename)
    clean_parent = clean_string(parent_dir)
    
    # Try different matching strategies
    for key, book in audiobooks.items():
        clean_title = clean_string(book['title'])
        clean_author = clean_string(book['author'])
        
        # Strategy 1: Check if both title and author are in the filepath
        if clean_title in clean_filename and clean_author in clean_parent:
            return key
            
        # Strategy 2: Check if title is in filename
        if clean_title in clean_filename:
            return key
            
        # Strategy 3: Check if author directory contains the book
        if clean_author in clean_parent and clean_title in clean_filename:
            return key
    
    return None

def process_audiobooks(csv_file, apple_music_path, verbose=True):
    """
    Process audiobook files and update their metadata for Apple Music
    
    Args:
        csv_file (str): Path to the Audible library CSV file
        apple_music_path (str): Path to Apple Music Media folder
        verbose (bool): Whether to print detailed debugging information
    """
    # Read the CSV file
    audiobooks = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Store full book info
            key = clean_string(row['Title'])  # Use cleaned title as key
            audiobooks[key] = {
                'title': row['Title'],
                'author': row['Authors'],
                'narrator': row['Narrators'],
                'series': row['Series Names'],
                'series_order': row['Series Order']
            }
    
    if verbose:
        print(f"Loaded {len(audiobooks)} audiobooks from CSV")
    
    # Setup audiobooks directory
    audiobooks_dir = os.path.join(apple_music_path, "Audiobooks")
    os.makedirs(audiobooks_dir, exist_ok=True)
    
    # Process files in Apple Music directory
    music_path = os.path.join(apple_music_path, "Music")
    
    # Keep track of processed files for reporting
    processed_files = []
    skipped_files = []
    
    for root, dirs, files in os.walk(music_path):
        for file in files:
            if file.lower().endswith('.mp3'):
                filepath = os.path.join(root, file)
                try:
                    # Try to match with audiobook data
                    book_key = find_matching_audiobook(filepath, audiobooks)
                    
                    if verbose:
                        print(f"\nAnalyzing file: {filepath}")
                        print(f"Parent directory: {os.path.basename(os.path.dirname(filepath))}")
                        if book_key:
                            print(f"Matched with book: {audiobooks[book_key]['title']}")
                        else:
                            print("No match found")
                    
                    if book_key:
                        book = audiobooks[book_key]
                        
                        # Create author directory in audiobooks folder
                        author_dir = os.path.join(audiobooks_dir, book['author'])
                        os.makedirs(author_dir, exist_ok=True)
                        
                        # Create book directory
                        book_dir = os.path.join(author_dir, book['title'])
                        os.makedirs(book_dir, exist_ok=True)
                        
                        # New file path
                        new_filepath = os.path.join(book_dir, file)
                        
                        # Copy file to new location
                        shutil.copy2(filepath, new_filepath)
                        
                        # Update metadata
                        try:
                            audio = EasyID3(new_filepath)
                        except mutagen.id3.ID3NoHeaderError:
                            audio = mutagen.File(new_filepath, easy=True)
                            if audio is None:
                                audio = EasyID3()
                                audio.save(new_filepath)
                        
                        # Update basic metadata
                        audio['title'] = book['title']
                        audio['artist'] = book['author']
                        audio['albumartist'] = book['narrator']
                        audio['album'] = book['title']
                        audio['genre'] = 'Audiobook'
                        audio['composer'] = book['narrator']
                        
                        # If part of a series, include in album
                        if book['series']:
                            audio['album'] = f"{book['series']} - {book['title']}"
                        
                        # Save the easy ID3 tags
                        audio.save()
                        
                        # Set additional ID3 tags
                        audio_full = ID3(new_filepath)
                        audio_full.add(TMED(encoding=3, text=['Audiobook']))
                        audio_full.add(TCMP(encoding=3, text=['1']))
                        audio_full.save()
                        
                        processed_files.append(file)
                        if verbose:
                            print(f"Successfully processed: {file}")
                    else:
                        skipped_files.append(file)
                
                except Exception as e:
                    print(f"Error processing {file}: {str(e)}")
                    skipped_files.append(file)
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Total files processed: {len(processed_files)}")
    print(f"Total files skipped: {len(skipped_files)}")
    
    if verbose and processed_files:
        print("\nProcessed files:")
        for file in processed_files:
            print(f"- {file}")
    
    if verbose and len(processed_files) == 0:
        print("\nNo files were processed. Here are the first 10 skipped files:")
        for file in skipped_files[:10]:
            print(f"- {file}")
    
    print("\nProcessed files have been moved to the Audiobooks directory in your Apple Music library.")
    print("Please refresh your Apple Music library to see the changes.")

if __name__ == "__main__":
    # Get user's home directory
    home = str(Path.home())
    
    # Set paths
    CSV_FILE = "liberation-library.csv"
    APPLE_MUSIC_PATH = os.path.join(home, "Music", "Music", "Media.localized")
    
    # Run the script with verbose output
    process_audiobooks(CSV_FILE, APPLE_MUSIC_PATH, verbose=True)
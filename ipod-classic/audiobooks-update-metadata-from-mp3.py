import os
import shutil
import mutagen
from mutagen.id3 import ID3, TMED, TCMP, TIT2, TPE1, TALB, TCON
from pathlib import Path
import glob
import re

class AudiobookProcessor:
    def __init__(self):
        self.home = str(Path.home())
        self.audiobooks_dir = os.path.join(
            self.home, "Music", "Music", "Media.localized", "Audiobooks"
        )
        self.processed_files = []
        self.skipped_files = []
        self.processed_artists = set()

    def setup_directories(self):
        """Ensure all necessary directories exist"""
        os.makedirs(self.audiobooks_dir, exist_ok=True)
        print(f"Audiobooks directory: {self.audiobooks_dir}")

    def get_metadata(self, filepath):
        """Get metadata from file, create if doesn't exist"""
        try:
            return ID3(filepath)
        except:
            try:
                # Create new ID3 tag if none exists
                audio = ID3()
                audio.save(filepath)
                return audio
            except Exception as e:
                print(f"Error creating ID3 tags for {filepath}: {str(e)}")
                return None

    def update_audiobook_metadata(self, filepath, existing_metadata=None):
        """Update metadata for both iPod Classic and modern Apple Books compatibility"""
        try:
            # Start with existing metadata or create new
            audio = existing_metadata if existing_metadata else self.get_metadata(filepath)
            if not audio:
                return False

            # Preserve existing core metadata
            title = str(audio.get('TIT2', ['Unknown Title'])[0])
            artist = str(audio.get('TPE1', ['Unknown Artist'])[0])
            album = str(audio.get('TALB', [title])[0])

            # Create new ID3 tags while preserving chapter information
            new_tags = ID3()
            
            # Copy over all existing tags first
            for key in audio.keys():
                if key.startswith('CHAP') or key.startswith('CTOC'):
                    new_tags.add(audio[key])

            # Update/add required tags for both systems
            new_tags.add(TIT2(encoding=3, text=[title]))
            new_tags.add(TPE1(encoding=3, text=[artist]))
            new_tags.add(TALB(encoding=3, text=[album]))
            new_tags.add(TCON(encoding=3, text=['Audiobook']))
            new_tags.add(TMED(encoding=3, text=['Audiobook']))
            new_tags.add(TCMP(encoding=3, text=['1']))

            # Save the updated metadata
            new_tags.save(filepath)
            return True

        except Exception as e:
            print(f"Error updating metadata for {filepath}: {str(e)}")
            return False

    def get_book_info(self, metadata):
        """Extract book information from metadata"""
        if not metadata:
            return None

        return {
            'title': str(metadata.get('TIT2', ['Unknown Title'])[0]),
            'artist': str(metadata.get('TPE1', ['Unknown Artist'])[0]),
            'album': str(metadata.get('TALB', ['Unknown Album'])[0])
        }

    def organize_file(self, source_path):
        """Organize a single audiobook file"""
        try:
            # Get existing metadata
            metadata = self.get_metadata(source_path)
            if not metadata:
                self.skipped_files.append(source_path)
                return False

            book_info = self.get_book_info(metadata)
            if not book_info:
                self.skipped_files.append(source_path)
                return False

            # Create artist directory
            artist_dir = os.path.join(self.audiobooks_dir, book_info['artist'])
            os.makedirs(artist_dir, exist_ok=True)

            # Create book directory
            book_dir = os.path.join(artist_dir, book_info['album'])
            os.makedirs(book_dir, exist_ok=True)

            # Copy file
            filename = os.path.basename(source_path)
            new_filepath = os.path.join(book_dir, filename)
            
            # If file already exists, add a number to prevent overwriting
            counter = 1
            while os.path.exists(new_filepath):
                base, ext = os.path.splitext(filename)
                new_filepath = os.path.join(book_dir, f"{base}_{counter}{ext}")
                counter += 1

            shutil.copy2(source_path, new_filepath)

            # Update metadata for both systems
            if self.update_audiobook_metadata(new_filepath, metadata):
                self.processed_files.append(source_path)
                self.processed_artists.add(book_info['artist'])
                print(f"Processed: {filename}")
                return True
            else:
                self.skipped_files.append(source_path)
                return False

        except Exception as e:
            print(f"Error organizing {source_path}: {str(e)}")
            self.skipped_files.append(source_path)
            return False

    def process_libation_folder(self, libation_path):
        """Process all audiobooks from Libation folder"""
        print(f"Scanning Libation folder: {libation_path}")
        
        # Find all MP3 files
        mp3_files = glob.glob(os.path.join(libation_path, "**", "*.mp3"), recursive=True)
        total_files = len(mp3_files)
        
        print(f"Found {total_files} MP3 files")
        
        # Process each file
        for index, filepath in enumerate(mp3_files, 1):
            print(f"\nProcessing file {index}/{total_files}")
            self.organize_file(filepath)

    def print_summary(self):
        """Print processing summary"""
        print("\nProcessing Summary:")
        print(f"Total files processed: {len(self.processed_files)}")
        print(f"Total files skipped: {len(self.skipped_files)}")
        print(f"Total artists processed: {len(self.processed_artists)}")
        
        print("\nProcessed artists:")
        for artist in sorted(self.processed_artists):
            print(f"- {artist}")
        
        print("\nNext steps:")
        print("For Apple Books:")
        print("1. Open Books app")
        print("2. File > Add to Library")
        print(f"3. Navigate to: {self.audiobooks_dir}")
        print("4. Select the audiobook files to import")
        
        print("\nFor iPod Classic:")
        print("1. Use iTunes 12.7 or earlier")
        print("2. File > Add to Library")
        print(f"3. Navigate to: {self.audiobooks_dir}")
        print("4. Connect iPod Classic")
        print("5. Select your iPod")
        print("6. Go to Audiobooks tab")
        print("7. Select books to sync")

def main():
    processor = AudiobookProcessor()
    
    # Setup directories
    processor.setup_directories()
    
    # Get Libation path
    libation_path = os.path.join(processor.home, "Libation")
    
    # Confirm paths
    print(f"\nLibation path: {libation_path}")
    print(f"Audiobooks will be organized in: {processor.audiobooks_dir}")
    
    # Confirm with user
    response = input("\nProceed with processing? (y/n): ")
    if response.lower() == 'y':
        processor.process_libation_folder(libation_path)
        processor.print_summary()
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()
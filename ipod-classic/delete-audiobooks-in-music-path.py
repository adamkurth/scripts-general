import os
import csv
import shutil
from pathlib import Path
import re

class MusicLibraryCleaner:
    def __init__(self):
        self.home = str(Path.home())
        self.media_path = os.path.join(self.home, "Music", "Music", "Media.localized")
        self.music_path = os.path.join(self.media_path, "Music")
        self.audiobooks_path = os.path.join(self.media_path, "Audiobooks")
        self.authors_to_remove = set()
        self.removed_folders = []
        self.skipped_folders = []

    def load_authors_from_csv(self, csv_file):
        """Load author names from the Libation CSV file"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Split authors if multiple are listed
                    authors = row['Authors'].split(',')
                    for author in authors:
                        # Clean up author name
                        clean_author = author.strip()
                        if clean_author:
                            self.authors_to_remove.add(clean_author)
                            # Add variations of the name
                            self.authors_to_remove.add(clean_author.lower())
                            self.authors_to_remove.add(clean_author.replace('.', ''))
                            self.authors_to_remove.add(clean_author.replace(',', ''))

            print(f"Loaded {len(self.authors_to_remove)} author names from CSV")
        except Exception as e:
            print(f"Error loading CSV file: {str(e)}")
            return False
        return True

    def should_remove_folder(self, folder_name):
        """Determine if folder should be removed based on author name"""
        folder_clean = folder_name.strip()
        folder_lower = folder_clean.lower()
        
        # Try different variations of the folder name
        variations = [
            folder_clean,
            folder_lower,
            folder_clean.replace('.', ''),
            folder_clean.replace(',', ''),
            re.sub(r'[^\w\s]', '', folder_lower)
        ]
        
        return any(var in self.authors_to_remove for var in variations)

    def scan_folders(self):
        """Scan music folders and return list of folders to remove"""
        to_remove = []
        
        try:
            # Get all directories in the Music folder
            music_dirs = [d for d in os.listdir(self.music_path) 
                         if os.path.isdir(os.path.join(self.music_path, d))]
            
            # Check each directory
            for dir_name in music_dirs:
                if self.should_remove_folder(dir_name):
                    full_path = os.path.join(self.music_path, dir_name)
                    to_remove.append((dir_name, full_path))
                
            return to_remove
        
        except Exception as e:
            print(f"Error scanning folders: {str(e)}")
            return []

    def remove_folders(self, folders_to_remove, dry_run=True):
        """Remove the specified folders"""
        for folder_name, folder_path in folders_to_remove:
            try:
                if dry_run:
                    print(f"Would remove: {folder_path}")
                    self.removed_folders.append(folder_path)
                else:
                    print(f"Removing: {folder_path}")
                    shutil.rmtree(folder_path)
                    self.removed_folders.append(folder_path)
            except Exception as e:
                print(f"Error removing {folder_path}: {str(e)}")
                self.skipped_folders.append(folder_path)

    def print_summary(self, dry_run=True):
        """Print summary of operations"""
        print("\nOperation Summary:")
        if dry_run:
            print("DRY RUN - No files were actually removed")
        print(f"Total folders marked for removal: {len(self.removed_folders)}")
        print(f"Total folders skipped: {len(self.skipped_folders)}")
        
        if self.removed_folders:
            print("\nFolders marked for removal:")
            for folder in sorted(self.removed_folders):
                print(f"- {os.path.basename(folder)}")
        
        if self.skipped_folders:
            print("\nFolders skipped due to errors:")
            for folder in sorted(self.skipped_folders):
                print(f"- {os.path.basename(folder)}")

def main():
    cleaner = MusicLibraryCleaner()
    
    # Verify paths
    print("Paths to be used:")
    print(f"Media path: {cleaner.media_path}")
    print(f"Music path: {cleaner.music_path}")
    print(f"Audiobooks path: {cleaner.audiobooks_path} (will be preserved)")
    
    # Confirm paths exist
    if not os.path.exists(cleaner.music_path):
        print("Error: Music path does not exist!")
        return
    
    # Get CSV file path
    csv_file = "liberation-library.csv"
    if not os.path.exists(csv_file):
        print(f"Error: Cannot find {csv_file}")
        return
    
    # Load authors
    if not cleaner.load_authors_from_csv(csv_file):
        return
    
    # Scan for folders to remove
    print("\nScanning music library...")
    folders_to_remove = cleaner.scan_folders()
    
    if not folders_to_remove:
        print("No matching folders found to remove.")
        return
    
    # First do a dry run
    print("\nPerforming dry run...")
    cleaner.remove_folders(folders_to_remove, dry_run=True)
    cleaner.print_summary(dry_run=True)
    
    # Ask for confirmation
    response = input("\nWould you like to proceed with actual removal? (y/n): ")
    if response.lower() == 'y':
        # Reset tracking lists before actual run
        cleaner.removed_folders = []
        cleaner.skipped_folders = []
        
        # Perform actual removal
        print("\nPerforming actual removal...")
        cleaner.remove_folders(folders_to_remove, dry_run=False)
        cleaner.print_summary(dry_run=False)
        
        print("\nCleaning complete!")
    else:
        print("\nOperation cancelled.")

if __name__ == "__main__":
    main()
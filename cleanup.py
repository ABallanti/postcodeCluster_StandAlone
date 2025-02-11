import os
import glob
import shutil

def cleanup_folders():
    """Clean up unnecessary files before building executable"""
    
    # Folders to empty (but keep)
    folders_to_empty = ['static', 'uploads','build','dist']
    
    # Spec files to remove
    spec_file = "Postcode_Clustering.spec"
    
    print("Starting cleanup process...")
    
    # Remove spec file if it exists
    if os.path.exists(spec_file):
        print(f"\nRemoving spec file: {spec_file}")
        os.remove(spec_file)
    
    # Empty folders that need to be kept
    for folder in folders_to_empty:
        if os.path.exists(folder):
            print(f"\nEmptying {folder} folder...")
            # Remove all files in the folder
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        print(f"Removed file: {item_path}")
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"Removed directory: {item_path}")
                except Exception as e:
                    print(f"Error removing {item_path}: {e}")
        else:
            print(f"\nCreating empty {folder} folder...")
            os.makedirs(folder)
    
    # Clean root directory pycache
    if os.path.exists('__pycache__'):
        print("\nRemoving root __pycache__...")
        shutil.rmtree('__pycache__')
    
    print("\nCleanup completed!")

if __name__ == "__main__":
    cleanup_folders() 

import os

def collect_code(start_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(start_dir):
            for file in files:
                if file.endswith('.py') or file.endswith('.txt') or file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, start_dir)
                    # Use forward slashes for consistency
                    rel_path = rel_path.replace(os.sep, '/')
                    
                    outfile.write(f"\n{'='*50}\n")
                    outfile.write(f"File: app/analyzers/{rel_path}\n")
                    outfile.write(f"{'='*50}\n\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"Error reading file: {e}\n")
                    
                    outfile.write("\n\n")

if __name__ == "__main__":
    target_dir = r"f:\Codeguard\backend\app"
    output_path = r"f:\Codeguard\backend\app_analyzers_code.txt"
    collect_code(target_dir, output_path)
    print(f"Code collected to {output_path}")

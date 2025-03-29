import pandas as pd
import os
import glob

folder_path = 'bulk1'  # 🔁 Change this to your folder path
output_file = 'merged_output.csv'

csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# Read and concatenate
merged_df = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index=True)

# Save the merged file
merged_df.to_csv(output_file, index=False)

print(f"✅ Merged {len(csv_files)} files into '{output_file}'")

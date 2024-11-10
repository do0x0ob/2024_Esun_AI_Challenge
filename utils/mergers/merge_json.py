import json
from pathlib import Path
from tqdm import tqdm

def merge_json_files(input_dir, category):
    merged_data = {}
    
    # 只獲取直接位於目錄下的 json 文件，不包括 merged 目錄中的文件
    file_paths = [f for f in input_dir.glob('*.json') if f.is_file()]
    
    for file_path in tqdm(file_paths, desc=f'合併 {category} 文件'):
        file_id = file_path.stem
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            merged_data[file_id] = content
        except Exception as e:
            print(f"處理文件 {file_path} 時發生錯誤: {e}")
    
    # 確保 merged 目錄存在
    merged_dir = input_dir / "merged"
    merged_dir.mkdir(exist_ok=True)
    
    output_path = merged_dir / f'merged_{category}_corpus.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    return output_path

if __name__ == "__main__":
    # 使用正確的路徑
    base_dir = Path("/Users/harperdelaviga/dataset_json")
    
    # 處理 finance 文件
    finance_dir = base_dir / "finance"
    if finance_dir.exists():
        finance_output = merge_json_files(finance_dir, "finance")
        print(f"Finance 文件已合併至：{finance_output}")
    
    # 處理 insurance 文件
    insurance_dir = base_dir / "insurance"
    if insurance_dir.exists():
        insurance_output = merge_json_files(insurance_dir, "insurance")
        print(f"Insurance 文件已合併至：{insurance_output}")
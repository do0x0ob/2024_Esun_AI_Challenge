import os
import json

def merge_txt_and_json(folder_path, json_file_path, output_file_path):
    # 讀取傳入的 JSON 檔案
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # 遍歷資料夾中的所有子資料夾與 .txt 檔案
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith('.txt'):
                file_key = filename.split('.')[0]
                txt_file_path = os.path.join(root, filename)
                
                # 讀取 .txt 檔案內容
                with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
                    content = txt_file.read()
                
                # 若 key 已存在於 JSON，則覆寫，否則新增
                data[file_key] = content

    # 將合併後的資料寫入新的 JSON 檔案
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

# 傳入路徑
folder_path = '/Users/harperdelaviga/finance_1106'  # .txt 檔案資料夾路徑
json_file_path = '/Users/harperdelaviga/dataset_json/ocr_json/ocr_finance.json'  # 原始 JSON 檔案路徑
output_file_path = '/Users/harperdelaviga/dataset_json/google_doc_json/dataset.json'  # Output JSON 檔案路徑

merge_txt_and_json(folder_path, json_file_path, output_file_path)

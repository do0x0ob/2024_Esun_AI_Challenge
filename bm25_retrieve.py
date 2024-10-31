import os
import json
import argparse

from tqdm import tqdm
import jieba
from rank_bm25 import BM25Okapi


def init_jieba():
    """初始化jieba分詞器，載入自定義字典"""
    # 載入自定義字典
    jieba.load_userdict("custom_dict.txt")


def load_data(source_path, category, use_merged=True):
    """載入參考資料，返回一個字典，key為檔案名稱，value為文本內容"""
    if use_merged:
        # 讀取合併版JSON檔
        merged_filename = f"merged_{category}_corpus.json"
        merged_path = os.path.join(source_path, category, 'merged', merged_filename)
        
        with open(merged_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 確保所有值都是字符串格式
            return {int(k): str(v) for k, v in data.items()}
    else:
        # 讀取分散的JSON檔
        category_path = os.path.join(source_path, category)
        corpus_dict = {}
        json_files = [f for f in os.listdir(category_path) if f.endswith('.json')]
        
        for file in tqdm(json_files):
            file_path = os.path.join(category_path, file)
            file_id = int(file.replace('.json', ''))
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                corpus_dict[file_id] = str(data.get('text', ''))
                
        return corpus_dict


def BM25_retrieve(qs, source, corpus_dict):
    """根據查詢語句和指定的來源，檢索答案"""
    try:
        # 確保查詢和語料庫文本都是字符串
        if isinstance(qs, bytes):
            qs = qs.decode('utf-8')
        else:
            qs = str(qs)

        filtered_corpus = []
        for file in source:
            text = corpus_dict[int(file)]
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            else:
                text = str(text)
            filtered_corpus.append(text)

        # 使用jieba進行分詞
        tokenized_corpus = [list(jieba.cut_for_search(doc)) for doc in filtered_corpus]
        bm25 = BM25Okapi(tokenized_corpus, b=0.5)
        tokenized_query = list(jieba.cut_for_search(qs))
        
        # 獲取最相關的文檔
        ans = bm25.get_top_n(tokenized_query, list(filtered_corpus), n=1)
        a = ans[0]
        
        # 找回對應的檔案名
        res = [key for key, value in corpus_dict.items() if str(value) == str(a)]
        return res[0]
    except Exception as e:
        print(f"Error in BM25_retrieve: {str(e)}")
        print(f"Query: {type(qs)}, Source: {type(source)}")
        print(f"Corpus_dict type: {type(corpus_dict)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some paths and files.')
    parser.add_argument('--question_path', type=str, required=True, help='讀取發布題目路徑')
    parser.add_argument('--source_path', type=str, required=True, help='讀取參考資料路徑')
    parser.add_argument('--output_path', type=str, required=True, help='輸出符合參賽格式的答案路徑')
    parser.add_argument('--use_merged', type=bool, default=True, help='是否使用合併版JSON檔')
    parser.add_argument('--dataset_json_path', type=str, 
                       default='/Users/harperdelaviga/dataset_json',
                       help='JSON檔案路徑')

    args = parser.parse_args()

    # 初始化jieba，載入自定義字典
    init_jieba()

    answer_dict = {"answers": []}

    with open(args.question_path, 'rb') as f:
        qs_ref = json.load(f)

    # 讀取保險和金融資料
    corpus_dict_insurance = load_data(args.dataset_json_path, 'insurance', use_merged=args.use_merged)
    corpus_dict_finance = load_data(args.dataset_json_path, 'finance', use_merged=args.use_merged)

    # 讀取FAQ資料
    with open(os.path.join(args.source_path, 'faq/pid_map_content.json'), 'rb') as f_s:
        key_to_source_dict = json.load(f_s)
        key_to_source_dict = {int(key): value for key, value in key_to_source_dict.items()}

    for q_dict in qs_ref['questions']:
        if q_dict['category'] == 'finance':
            retrieved = BM25_retrieve(q_dict['query'], q_dict['source'], corpus_dict_finance)
            answer_dict['answers'].append({"qid": q_dict['qid'], "retrieve": retrieved})

        elif q_dict['category'] == 'insurance':
            retrieved = BM25_retrieve(q_dict['query'], q_dict['source'], corpus_dict_insurance)
            answer_dict['answers'].append({"qid": q_dict['qid'], "retrieve": retrieved})

        elif q_dict['category'] == 'faq':
            corpus_dict_faq = {key: str(value) for key, value in key_to_source_dict.items() 
                             if key in q_dict['source']}
            retrieved = BM25_retrieve(q_dict['query'], q_dict['source'], corpus_dict_faq)
            answer_dict['answers'].append({"qid": q_dict['qid'], "retrieve": retrieved})

        else:
            raise ValueError("Something went wrong")

    # 將答案字典保存為json文件
    with open(args.output_path, 'w', encoding='utf8') as f:
        json.dump(answer_dict, f, ensure_ascii=False, indent=4)
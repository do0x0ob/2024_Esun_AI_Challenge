import os
import datetime
import json
import argparse
from tqdm import tqdm
import jieba
from rank_bm25 import BM25Okapi
import itertools

class BM25Tuner:
    def __init__(self, data_dir, dataset_json_path, use_custom_dict=False, use_synonyms=False, synonyms_dir=None, use_stopwords=False, stopwords_path=None):
        self.data_dir = data_dir
        self.dataset_json_path = dataset_json_path
        self.output_path = os.path.join(os.getcwd(), 'output_answers.json')
        self.best_params = None
        self.best_accuracy = 0
        self.results = []

        # 停用詞相關設定
        self.use_stopwords = use_stopwords
        self.stopwords_path = stopwords_path
        self.stopwords = set()
        if use_stopwords:
            self.load_stopwords()

        # 同義詞相關設定
        self.use_synonyms = use_synonyms
        self.synonyms_dir = synonyms_dir
        self.synonyms = {}
        if use_synonyms:
            self.load_synonyms()
        
        # 初始化 jieba 自定義字典
        if use_custom_dict:
            self.init_jieba()
        
        print("Loading all data...")
        self.load_json_data()
        print("Data loading completed!")

    #TODO: testing
    def test_stopwords(self, test_text="在這裡測試停用詞的效果"):
        """測試停用詞效果"""
        print("\n=== Stopwords Test ===")
        print(f"Test text: {test_text}")
        print(f"Stopwords enabled: {self.use_stopwords}")
        print(f"Stopwords path: {self.stopwords_path}")
        print(f"Total stopwords loaded: {len(self.stopwords)}")
        print(f"Current stopwords: {list(self.stopwords)[:10]}")  # 顯示前10個停用詞
        
        # 測試分詞
        tokens = list(jieba.cut_for_search(test_text))
        print(f"Original tokens: {tokens}")
        
        # 測試停用詞移除
        filtered_tokens = self.remove_stopwords(tokens)
        print(f"Tokens after stopwords removal: {filtered_tokens}")
        
        # 顯示被移除的詞
        removed = [t for t in tokens if t not in filtered_tokens]
        print(f"Removed tokens: {removed}")
        
        # 顯示每個詞是否在停用詞中
        print("\nToken analysis:")
        for token in tokens:
            print(f"Token '{token}' is{' ' if token in self.stopwords else ' not '}in stopwords")

    def load_stopwords(self):
        """載入停用詞"""
        self.stopwords = set()  # 確保初始化為空集合
        
        if not self.stopwords_path:
            print("No stopwords path specified")
            return
        
        try:
            with open(self.stopwords_path, 'r', encoding='utf-8') as f:
                # 直接讀取所有非空行
                self.stopwords = {line.strip() for line in f if line.strip()}
                
            print(f"Stopwords enabled: {bool(self.stopwords)}")
            print(f"Stopwords path: {self.stopwords_path}")
            print(f"Total stopwords loaded: {len(self.stopwords)}")
            print(f"Current stopwords: {list(self.stopwords)[:10]}")  # 只顯示前10個作為預覽
            
        except FileNotFoundError:
            print(f"Error: Stopwords file not found at {self.stopwords_path}")
        except Exception as e:
            print(f"Error loading stopwords: {str(e)}")

    def remove_stopwords(self, tokens):
        """移除停用詞"""
        if not self.use_stopwords:
            return tokens
        
        # original_length = len(tokens)
        filtered_tokens = [token for token in tokens if token not in self.stopwords]
        # removed_tokens = [token for token in tokens if token in self.stopwords]
        
        # TODO: debug print only
        """
        if removed_tokens:  # 只有在實際移除了停用詞時才打印
            print(f"Stopwords removal - Before: {original_length} tokens, After: {len(filtered_tokens)} tokens")
            print(f"Removed tokens: {removed_tokens}")
        """
            
        return filtered_tokens

    def read_synonyms_from_file(self, file_path):
        """讀取同義詞字典文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                synonyms = json.load(f)
                print(f"Loaded synonym dictionary: {json.dumps(synonyms, ensure_ascii=False, indent=2)}")
                return synonyms
        except Exception as e:
            print(f"Error loading synonyms from {file_path}: {e}")
            return {}

    
    def load_synonyms(self):
        """載入同義詞字典"""
        if not self.synonyms_dir:
            print("No synonyms directory specified, using default 'synonyms' directory")
            self.synonyms_dir = os.path.dirname(__file__)

        # 更改為讀取 JSON 格式的同義詞字典
        synonym_file_path = os.path.join(self.synonyms_dir, 'synonym_dict.json')
        if os.path.exists(synonym_file_path):
            self.synonyms = self.read_synonyms_from_file(synonym_file_path)
            print(f"Loaded synonyms from {synonym_file_path}")
        else:
            print(f"Warning: Synonym file not found at {synonym_file_path}")
        

    def _load_synonym_file(self, file_path):
        """從單個文件載入同義詞典"""
        synonyms = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    words = line.split()
                    if len(words) > 1:
                        key_word = words[0]
                        synonyms[key_word] = words[1:]
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
        return synonyms
    
    def expand_query_with_weight(self, query, category):
        """擴展查詢字串，加入同義詞並賦予權重"""
        if not self.synonyms or category not in self.synonyms:
            return query, {}

        words = list(jieba.cut_for_search(query))
        expanded_words = []
        weight_dict = {}
        used_synonyms = set()
        
        i = 0
        while i < len(words):
            # 先嘗試匹配較長的詞組
            found_phrase = False
            for j in range(min(3, len(words) - i), 0, -1):
                phrase = ''.join(words[i:i+j])
                if phrase in self.synonyms[category]:
                    if phrase not in used_synonyms:
                        # 獲取詞組資訊
                        phrase_data = self.synonyms[category][phrase]
                        weight = phrase_data["weight"]
                        
                        # 添加原詞組
                        expanded_words.append(phrase)
                        weight_dict[phrase] = weight
                        used_synonyms.add(phrase)
                        
                        # 添加同義詞
                        for syn in phrase_data["synonyms"]:
                            if syn not in used_synonyms:
                                expanded_words.append(syn)
                                weight_dict[syn] = weight
                                used_synonyms.add(syn)
                                
                    i += j
                    found_phrase = True
                    break
            
            # 如果沒找到詞組，處理單個詞
            if not found_phrase:
                word = words[i]
                if word not in used_synonyms:
                    expanded_words.append(word)
                    
                    # 檢查是否有同義詞
                    if word in self.synonyms[category]:
                        word_data = self.synonyms[category][word]
                        weight = word_data["weight"]
                        weight_dict[word] = weight
                        
                        # 添加同義詞
                        for syn in word_data["synonyms"]:
                            if syn not in used_synonyms:
                                expanded_words.append(syn)
                                weight_dict[syn] = weight
                                used_synonyms.add(syn)
                                
                    used_synonyms.add(word)
                i += 1

        expanded_query = ' '.join(expanded_words)
        return expanded_query, weight_dict

    def init_jieba(self):
        """初始化 jieba 分詞器"""
        try:
            dict_path = 'custom_dict.txt'
            if not os.path.exists(dict_path):
                raise FileNotFoundError(f"Custom dictionary not found at: {dict_path}")
            
            # 載入前先觀察詞典內容
            print("Loading custom dictionary...")
            with open(dict_path, 'r', encoding='utf-8') as f:
                print(f.read())
                
            jieba.load_userdict(dict_path)
            print("Custom dictionary loaded successfully!")
            
            # 測試是否真的載入成功
            # test_text = "契約內容變更應經雙方同意並批註"
            # print("Test segmentation:", list(jieba.cut(test_text)))
            
        except Exception as e:
            print(f"Error loading custom dictionary: {str(e)}")
            print("Continuing with default dictionary...")

    def load_json_data(self):
            """載入所有必要的 JSON 資料"""
            try:
                # 構建完整路徑
                insurance_path = os.path.join(self.dataset_json_path, 'ocr_json', 'ocr_insurance.json')
                # TODO: path
                # finance_path = os.path.join(self.dataset_json_path, 'ocr_json', 'ocr_finance.json')
                finance_path = os.path.join(self.dataset_json_path, 'google_doc_json', 'dataset.json')
                faq_path = os.path.join(self.data_dir, 'reference', 'faq', 'pid_map_content.json')
                # TODO:
                questions_path = os.path.join(self.data_dir, 'dataset', 'preliminary', 'questions_example.json')
                ground_truth_path = os.path.join(self.data_dir, 'dataset', 'preliminary', 'ground_truths_example.json')
                # questions_path = os.path.join(self.data_dir, 'dataset', 'preliminary', 'extra_question.json')
                # ground_truth_path = os.path.join(self.data_dir, 'dataset', 'preliminary', 'extra_ground_truth.json')

                # 載入資料
                with open(insurance_path, 'r', encoding='utf-8') as f:
                    self.corpus_dict_insurance = {int(k): str(v) for k, v in json.load(f).items()}

                with open(finance_path, 'r', encoding='utf-8') as f:
                    self.corpus_dict_finance = {int(k): str(v) for k, v in json.load(f).items()}

                with open(faq_path, 'r', encoding='utf-8') as f:
                    self.key_to_source_dict = {int(k): str(v) for k, v in json.load(f).items()}

                with open(questions_path, 'r', encoding='utf-8') as f:
                    self.questions = json.load(f)
                    
                with open(ground_truth_path, 'r', encoding='utf-8') as f:
                    self.ground_truth = json.load(f)

                # 初始化 tokenized corpus
                self._init_tokenized_corpus()

            except Exception as e:
                print("\nError loading data:")
                print(f"Error type: {type(e).__name__}")
                print(f"Error message: {str(e)}")
                raise


    def _init_tokenized_corpus(self):
        """初始化並處理 tokenized corpus"""
        self.tokenized_corpus = {
            'insurance': {},
            'finance': {},
            'faq': {}
        }
        
        for doc_id, content in self.corpus_dict_insurance.items():
            tokens = list(jieba.cut_for_search(content))
            self.tokenized_corpus['insurance'][doc_id] = self.remove_stopwords(tokens)
        
        for doc_id, content in self.corpus_dict_finance.items():
            tokens = list(jieba.cut_for_search(content))
            self.tokenized_corpus['finance'][doc_id] = self.remove_stopwords(tokens)
            
        for doc_id, content in self.key_to_source_dict.items():
            tokens = list(jieba.cut_for_search(str(content)))
            self.tokenized_corpus['faq'][doc_id] = self.remove_stopwords(tokens)


    def check_file_exists(self, file_path, description):
        """檢查文件是否存在並提供詳細的錯誤訊息"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{description} not found at: {file_path}\n"
                                f"Current working directory: {os.getcwd()}\n"
                                f"Data directory: {self.data_dir}\n"
                                f"Dataset JSON path: {self.dataset_json_path}")
        return True

    def BM25_retrieve(self, qs, source, category, k1=1.5, b=0.75, n=1):
        """使用 BM25 算法檢索文檔"""
        expanded_query = self.expand_query_with_weight(qs, category) # expand_query_with_weight | expand_query
        
        if category == 'finance':
            tokenized_docs = [self.tokenized_corpus['finance'][int(file)] for file in source]
            filtered_corpus = [self.corpus_dict_finance[int(file)] for file in source]
        elif category == 'insurance':
            tokenized_docs = [self.tokenized_corpus['insurance'][int(file)] for file in source]
            filtered_corpus = [self.corpus_dict_insurance[int(file)] for file in source]
        else:  # faq
            tokenized_docs = [self.tokenized_corpus['faq'][int(file)] for file in source]
            filtered_corpus = [str(self.key_to_source_dict[int(file)]) for file in source]

        bm25 = BM25Okapi(tokenized_docs, k1=k1, b=b)
        # query_tokens = list(jieba.cut_for_search(expanded_query))
        # TODO: testing
        print(f"Expanded query in BM25_retrieve: {expanded_query}")
        query_tokens = list(jieba.cut_for_search(expanded_query))
        doc_scores = bm25.get_scores(query_tokens)
        best_idx = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:n]
        
        # Match with original text
        best_doc = filtered_corpus[best_idx[0]]
        
        # Return corresponding file ID
        if category == 'finance':
            res = [key for key, value in self.corpus_dict_finance.items() if value == best_doc]
        elif category == 'insurance':
            res = [key for key, value in self.corpus_dict_insurance.items() if value == best_doc]
        else:  # faq
            res = [key for key, value in self.key_to_source_dict.items() if str(value) == best_doc]
        
        return res[0]
    
    def BM25_retrieve_with_weight(self, qs, source, category, k1=1.5, b=0.75, n=1):
        """使用加權 BM25 算法檢索文檔"""
        log_filename = "bm25_debug.log"
        with open(log_filename, 'a', encoding='utf-8') as log_file:
            log_file.write("\n" + "="*50 + "\n")
            log_file.write(f"Timestamp: {datetime.datetime.now()}\n\n")
            
            # 獲取擴展查詢和權重
            expanded_query, weight_dict = self.expand_query_with_weight(qs, category)
            
            log_file.write(f"Original query: {qs}\n")
            log_file.write(f"Category: {category}\n")
            log_file.write(f"Expanded query: {expanded_query}\n")
            log_file.write(f"Weight dictionary: {json.dumps(weight_dict, ensure_ascii=False, indent=2)}\n\n")

            # 選擇相應的語料庫
            if category == 'finance':
                tokenized_docs = [self.tokenized_corpus['finance'][int(file)] for file in source]
                filtered_corpus = [self.corpus_dict_finance[int(file)] for file in source]
            elif category == 'insurance':
                tokenized_docs = [self.tokenized_corpus['insurance'][int(file)] for file in source]
                filtered_corpus = [self.corpus_dict_insurance[int(file)] for file in source]
            else:  # faq
                tokenized_docs = [self.tokenized_corpus['faq'][int(file)] for file in source]
                filtered_corpus = [str(self.key_to_source_dict[int(file)]) for file in source]

            # 創建 BM25 實例
            bm25 = BM25Okapi(tokenized_docs, k1=k1, b=b)
            
            # 對查詢進行分詞並應用權重
            query_tokens = list(jieba.cut_for_search(expanded_query))
            query_tokens = self.remove_stopwords(query_tokens)
            
            # 記錄查詢詞和權重
            log_file.write("Query Analysis:\n")
            log_file.write(f"Query tokens (after stopwords removal): {query_tokens}\n")
            
            # 創建加權查詢向量
            weighted_query = []
            query_weights = []
            for token in query_tokens:
                weight = weight_dict.get(token, 1.0)  # 默認權重為1.0
                weighted_query.append(token)
                query_weights.append(weight)
                log_file.write(f"Token: {token}, Weight: {weight}\n")
            
            # 獲取基礎 BM25 分數
            base_scores = bm25.get_scores(weighted_query)
            
            # 應用權重到文檔評分
            weighted_scores = []
            log_file.write("\nDocument Scoring Details:\n")
            
            for doc_idx, base_score in enumerate(base_scores):
                doc_tokens = tokenized_docs[doc_idx]
                log_file.write(f"\nDocument {doc_idx}:\n")
                log_file.write(f"Content preview: {' '.join(doc_tokens[:50])}...\n")
                
                # 計算文檔的加權分數
                weighted_score = 0
                token_matches = []
                
                # 對每個查詢詞
                for q_token, q_weight in zip(weighted_query, query_weights):
                    # 計算該詞在文檔中的 TF-IDF 得分
                    term_score = bm25.get_scores([q_token])[doc_idx]
                    # 應用權重
                    weighted_term_score = term_score * q_weight
                    weighted_score += weighted_term_score
                    
                    if term_score > 0:
                        token_matches.append({
                            'token': q_token,
                            'weight': q_weight,
                            'base_score': term_score,
                            'weighted_score': weighted_term_score
                        })
                
                # 記錄評分細節
                log_file.write("Term matching details:\n")
                for match in token_matches:
                    log_file.write(f"  - Token: {match['token']}\n")
                    log_file.write(f"    Weight: {match['weight']}\n")
                    log_file.write(f"    Base score: {match['base_score']:.4f}\n")
                    log_file.write(f"    Weighted score: {match['weighted_score']:.4f}\n")
                
                log_file.write(f"Base score: {base_score:.4f}\n")
                log_file.write(f"Final weighted score: {weighted_score:.4f}\n")
                log_file.write("-" * 40 + "\n")
                
                weighted_scores.append(weighted_score)

            # 選擇最佳文檔
            best_idx = sorted(range(len(weighted_scores)), key=lambda i: weighted_scores[i], reverse=True)[:n]
            best_doc = filtered_corpus[best_idx[0]]
            
            # 返回對應的文件 ID
            if category == 'finance':
                res = [key for key, value in self.corpus_dict_finance.items() if value == best_doc]
            elif category == 'insurance':
                res = [key for key, value in self.corpus_dict_insurance.items() if value == best_doc]
            else:  # faq
                res = [key for key, value in self.key_to_source_dict.items() if str(value) == best_doc]
            
            log_file.write(f"\nSelected document ID: {res[0]}\n")
            log_file.write(f"Selected document content: {best_doc[:200]}...\n")
            log_file.write("=" * 50 + "\n\n")

        return res[0]

    def evaluate_parameters(self, params):
        """Evaluate performance for given parameter set"""
        answer_dict = {"answers": []}
        
        for q_dict in self.questions['questions']:
            retrieved = self.BM25_retrieve_with_weight( # BM25_retrieve_with_weight | BM25_retrieve
                q_dict['query'], 
                q_dict['source'], 
                q_dict['category'],
                k1=params['k1'],
                b=params['b'],
                n=params['n']
            )
            
            answer_dict['answers'].append({
                "qid": q_dict['qid'],
                "retrieve": retrieved
            })

        # Calculate accuracy
        correct_count = 0
        total_count = len(self.ground_truth['ground_truths'])

        for output_answer in answer_dict['answers']:
            qid = output_answer['qid']
            retrieve = output_answer['retrieve']
            gt_answer = next((item for item in self.ground_truth['ground_truths'] if item['qid'] == qid), None)
            if gt_answer and gt_answer['retrieve'] == retrieve:
                correct_count += 1

        accuracy = correct_count / total_count
        return accuracy, answer_dict

    def grid_search(self, param_grid):
        """Perform grid search for parameter tuning"""
        print("\nStarting grid search...")
        total_combinations = len(list(itertools.product(*param_grid.values())))
        print(f"Total parameter combinations to test: {total_combinations}")
        
        for params in tqdm(itertools.product(*param_grid.values()), total=total_combinations):
            param_dict = dict(zip(param_grid.keys(), params))
            accuracy, answer_dict = self.evaluate_parameters(param_dict)
            
            self.results.append({
                'params': param_dict,
                'accuracy': accuracy
            })

            if accuracy > self.best_accuracy:
                self.best_accuracy = accuracy
                self.best_params = param_dict
                # Save best results
                with open(self.output_path, 'w', encoding='utf8') as f:
                    json.dump(answer_dict, f, ensure_ascii=False, indent=4)

            print(f"\nParameters: {param_dict}")
            print(f"Accuracy: {accuracy:.2%}")

        print("\nGrid search completed!")
        print(f"Best parameters: {self.best_params}")
        print(f"Best accuracy: {self.best_accuracy:.2%}")

        # 對最佳結果進行錯誤分析
        best_answer_dict = None
        for result in self.results:
            if result['accuracy'] == self.best_accuracy:
                # 重新運行最佳參數來獲取答案
                best_params = result['params']
                best_answer_dict = self.evaluate_parameters(best_params)[1]
                break
        
        if best_answer_dict:
            self.analyze_errors(best_answer_dict)

        # Save all results
        with open('parameter_search_results.json', 'w', encoding='utf8') as f:
            json.dump({
                'best_params': self.best_params,
                'best_accuracy': self.best_accuracy,
                'all_results': self.results
            }, f, ensure_ascii=False, indent=4)
    
    def analyze_errors(self, answer_dict):
        """分析錯誤案例"""
        print("\n=== Error Analysis ===")
        errors = []
        
        for output_answer in answer_dict['answers']:
            qid = output_answer['qid']
            predicted = output_answer['retrieve']
            
            # 找到對應的ground truth
            gt_answer = next((item for item in self.ground_truth['ground_truths'] if item['qid'] == qid), None)
            if gt_answer and gt_answer['retrieve'] != predicted:
                # 找到原始問題
                question = next((q for q in self.questions['questions'] if q['qid'] == qid), None)
                
                if question:
                    # 獲取預測文本和正確文本
                    predicted_text = ""
                    correct_text = ""
                    if question['category'] == 'finance':
                        predicted_text = self.corpus_dict_finance.get(predicted, "Not found")
                        correct_text = self.corpus_dict_finance.get(gt_answer['retrieve'], "Not found")
                    elif question['category'] == 'insurance':
                        predicted_text = self.corpus_dict_insurance.get(predicted, "Not found")
                        correct_text = self.corpus_dict_insurance.get(gt_answer['retrieve'], "Not found")
                    else:  # faq
                        predicted_text = self.key_to_source_dict.get(predicted, "Not found")
                        correct_text = self.key_to_source_dict.get(gt_answer['retrieve'], "Not found")
                    
                    errors.append({
                        'qid': qid,
                        'category': question['category'],
                        'query': question['query'],
                        'predicted_id': predicted,
                        'correct_id': gt_answer['retrieve'],
                        'predicted_text': predicted_text,
                        'correct_text': correct_text,
                        'tokenized_query': list(jieba.cut_for_search(question['query']))
                    })
        
        # 輸出錯誤分析
        print(f"\nTotal errors: {len(errors)}")
        print("\nError distribution by category:")
        category_counts = {}
        for error in errors:
            category_counts[error['category']] = category_counts.get(error['category'], 0) + 1
        for category, count in category_counts.items():
            print(f"{category}: {count} errors")
        
        # 保存詳細錯誤分析
        with open('error_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        
        return errors
    
def main():
    parser = argparse.ArgumentParser(description="Tune BM25 parameters")
    parser.add_argument("--data_dir", 
                       required=True, 
                       help="Path to the directory containing the dataset")
    parser.add_argument("--config", 
                       default="param_config.json", 
                       help="Path to configuration file")
    parser.add_argument("--use_custom_dict", 
                       action="store_true", 
                       help="Whether to use custom dictionary")
    parser.add_argument("--use_synonyms", 
                       action="store_true", 
                       help="Whether to use synonyms expansion")
    parser.add_argument("--dataset_json_path", 
                       required=True, 
                       help="Path to JSON dataset")
    parser.add_argument("--synonyms_dir", 
                       default="synonyms",
                       help="Path to synonyms directory")
    parser.add_argument("--use_stopwords",
                       action="store_true",
                       help="Whether to use stopwords")
    parser.add_argument("--stopwords_path",
                       default="stopwords.txt",
                       help="Path to stopwords file")
    args = parser.parse_args()

    # Load configuration
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        param_grid = config['param_grid']
        print("Loaded parameter grid from config file:")
        print(json.dumps(param_grid, indent=2))
    except FileNotFoundError:
        print(f"Config file {args.config} not found, using default parameters")
        param_grid = {
            'k1': [0.5, 1.5],
            'b': [0.25, 0.75],
            'n': [1, 2]
        }
    except json.JSONDecodeError:
        print(f"Error parsing config file {args.config}, using default parameters")
        param_grid = {
            'k1': [0.5, 1.5],
            'b': [0.25, 0.75],
            'n': [1, 2]
        }

    # Print configuration
    print("\nRunning with configuration:")
    print(f"Data directory: {args.data_dir}")
    print(f"Dataset JSON path: {args.dataset_json_path}")
    print(f"Using custom dictionary: {args.use_custom_dict}")
    print(f"Using synonyms expansion: {args.use_synonyms}")
    if args.use_synonyms:
        print(f"Synonyms directory: {args.synonyms_dir}")

    # Initialize tuner
    try:
        tuner = BM25Tuner(
            data_dir=args.data_dir,
            dataset_json_path=args.dataset_json_path,
            use_custom_dict=args.use_custom_dict,
            use_synonyms=args.use_synonyms,
            synonyms_dir=args.synonyms_dir if args.use_synonyms else None,
            use_stopwords=args.use_stopwords,
            stopwords_path=args.stopwords_path if args.use_stopwords else None
        )

        # TODO: test only 添加停用詞測試
        """
        test_texts = [
            "在這裡測試停用詞",
            "我在想知道保險的內容",
            "這是一個、測試，在哪裡？",
        ]

        for text in test_texts:
            tuner.test_stopwords(text)
        """
        
        # Run grid search
        print("\nStarting parameter tuning...")
        tuner.grid_search(param_grid)
        
        # Print final results
        print("\nTuning completed!")
        print(f"Best parameters found: {tuner.best_params}")
        print(f"Best accuracy achieved: {tuner.best_accuracy:.2%}")
        print(f"Results saved to: {tuner.output_path}")
        print("Error analysis saved to: error_analysis.json")
        print("Parameter search results saved to: parameter_search_results.json")
        
    except Exception as e:
        print("\nError during execution:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        raise

if __name__ == "__main__":
    main()
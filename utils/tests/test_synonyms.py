import jieba
from rank_bm25 import BM25Okapi

class BM25Synonyms:
    def __init__(self):
        # 初始化同義詞典
        self.init_synonyms()
        
        # 載入測試資料
        self.load_test_data()
        print("Data loading completed!")
        
        # 測試模式下的結果儲存
        self.test_results = []

    def init_synonyms(self):
        """初始化同義詞詞典"""
        self.synonyms = {
            # 保險合約相關
            '契約內容': ['保單內容', '合約內容'],
            '契約': ['保單', '合約'],
            '變更': ['修改', '更改'],
            '批註': ['批示', '簽註'],
            '同意': ['核准', '許可'],
            
            # 保險身份相關
            '要保人': ['投保人', '保戶'],
            '被保險人': ['受保人'],
            '受益人': ['保險金受益人'],
            
            # 保險操作相關
            '申請': ['辦理', '提出'],
            '送達': ['遞交', '提交'],
            '檢具': ['準備', '具備']
        }

    def load_test_data(self):
        """載入測試資料"""
        self.corpus_dict_insurance = {
            186: "南山人壽威美鑽美元利率變動型終身壽險(定期給付型)_SYUL保險公司者,不得對抗保險公司。前項受益人的變更,於要保人檢具申請書及被保險人的同意書(要、被保險人為同一人時為申請書或電子申請文件)送達本公司時,本公司應即予批註或發給批註書。",
            627: "南山人壽新多福保美元利率變動型終身保險(定期給付型)_BUPL50南山人壽保險股份有限公司(以下簡稱「本公司」)南山人壽新多福保美元利率變動型終身保險(定期給付型)(樣本)滿期保險金、增值回饋分享金身故保險金或喪葬費用保險金、完全失能保險金"
        }

    def expand_query(self, query):
        """擴展查詢字串，加入同義詞"""
        words = list(jieba.cut(query))
        expanded_words = []
        used_synonyms = set()  # 追蹤已使用的同義詞
        
        i = 0
        while i < len(words):
            # 先嘗試匹配較長的詞組
            found_phrase = False
            for j in range(min(3, len(words) - i), 0, -1):
                phrase = ''.join(words[i:i+j])
                if phrase in self.synonyms:
                    if phrase not in used_synonyms:
                        expanded_words.append(phrase)
                        # 只加入未使用過的同義詞
                        for syn in self.synonyms[phrase]:
                            if syn not in used_synonyms:
                                expanded_words.append(syn)
                                used_synonyms.add(syn)
                        used_synonyms.add(phrase)
                    i += j
                    found_phrase = True
                    break
            
            if not found_phrase:
                word = words[i]
                if word not in used_synonyms:
                    expanded_words.append(word)
                    if word in self.synonyms:
                        for syn in self.synonyms[word]:
                            if syn not in used_synonyms:
                                expanded_words.append(syn)
                                used_synonyms.add(syn)
                    used_synonyms.add(word)
                i += 1
        
        return ' '.join(expanded_words)

    def test_single_query(self, query, correct_id, category='insurance'):
        """測試單一查詢"""
        # 擴展查詢
        expanded_query = self.expand_query(query)
        print(f"\nOriginal query: {query}")
        print(f"Expanded query: {expanded_query}")
        
        # 準備文檔
        tokenized_docs = [list(jieba.cut(doc)) for doc in self.corpus_dict_insurance.values()]
        
        # BM25 檢索
        bm25 = BM25Okapi(tokenized_docs)
        query_tokens = list(jieba.cut(expanded_query))
        doc_scores = bm25.get_scores(query_tokens)
        
        # 取得最佳匹配
        best_idx = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[0]
        predicted_id = list(self.corpus_dict_insurance.keys())[best_idx]
        
        # 儲存結果
        result = {
            'query': query,
            'expanded_query': expanded_query,
            'predicted_id': predicted_id,
            'correct_id': correct_id,
            'is_correct': predicted_id == correct_id,
            'predicted_text': self.corpus_dict_insurance[predicted_id][:100] + "...",
            'correct_text': self.corpus_dict_insurance[correct_id][:100] + "..."
        }
        
        # 顯示結果
        print(f"\nPredicted ID: {predicted_id}")
        print(f"Correct ID: {correct_id}")
        print(f"Is correct: {result['is_correct']}")
        print(f"\nPredicted text: {result['predicted_text']}")
        print(f"Correct text: {result['correct_text']}")
        
        return result

def main():
    # 測試案例
    test_cases = [
        {
            'query': "本契約內容的變更應經由誰同意並批註？",
            'correct_id': 186,
            'category': 'insurance'
        }
    ]
    
    # 初始化測試環境
    tester = BM25Synonyms()
    
    # 運行測試
    for case in test_cases:
        result = tester.test_single_query(
            query=case['query'],
            correct_id=case['correct_id'],
            category=case['category']
        )
    
    print(result)

if __name__ == "__main__":
    main()
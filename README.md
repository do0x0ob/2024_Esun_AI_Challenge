## Performance
Accuracy for extra questions = **64.00%**
Accuracy for official example questions = **80.67%**

## todo

**1. 差異和對錯情況整理**
| QID | Ground Truth | old_output_answers | new_output_answers | 答對者           | 已處理？ |
|-----|--------------|--------------------|---------------------|------------------|-------|
| 56  | 171          | 760                | 171                | new_output_answers | [  ]   |
| 69  | 981          | 981                | 182                | old_output_answers | [  ]   |
| 72  | 204          | 932                | 442                | 兩者皆答錯         | [  ]   |
| 86  | 189          | 189                | 525                | old_output_answers | [  ]   |
| 89  | 793          | 999                | 515                | 兩者皆答錯         | [  ]   |
| 95  | 307          | 307                | 87                 | old_output_answers | [  ]   |
| 96  | 435          | 435                | 750                | old_output_answers | [  ]   |
| 97  | 282          | 579                | 444                | 兩者皆答錯         | [  ]   |
  
**2. 嘗試項目**  
[ ] 1. 交叉比對一下錯題，針對單一文件哪個資料集好就用哪一版。  
[ ] 2. 針對新的資料加上昨天的去空格、換行整理看看會不會比較好  
[ ] 3. 加上 451-750 後比較。  

---

## How to Use

1. **bm25_tuner 運行**:  

    ```
    python bm25_tuner.py \
    --data_dir path/to/data \
    --config config.json \
    --dataset_json_path path/to/ocr_json \
    --use_custom_dict
    --use_synonyms
    ```

2. **Run bm25_retrieve**  
    ```
    python bm25_retrieve.py \                                           
    --question_path /Users/harperdelaviga/競賽資料集/dataset/preliminary/questions_example.json \
    --source_path /Users/harperdelaviga/競賽資料集/reference \
    --output_path ./output_answers.json \
    --use_merged True \
    --dataset_json_path /Users/harperdelaviga/dataset_json
    ```

3. **answer_checker**  
    ```
    python answer_checker.py --data_dir /Users/harperdelaviga/競賽資料集
    ```

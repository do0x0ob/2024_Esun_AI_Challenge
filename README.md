## Performance
Accuracy = 72%


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

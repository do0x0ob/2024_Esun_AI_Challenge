## Performance  
**Best accuracy achieved: 84.67%**  

## Error Analysis

**Total errors: 23**

**Error distribution by category:**  
- insurance: 3 errors  
- finance: 17 errors  
- faq: 3 errors

Best parameters found: {'k1': 0.8, 'b': 0.45, 'n': 1}  

## How to Use

**Run bm25_tuner in terminal**

```shell
python bm25_tuner.py \
    --data_dir ../競賽資料集 \
    --config param_config.json \
    --dataset_json_path ../dataset_json \
    --use_custom_dict \
        --use_synonyms \
    --synonyms_dir synonyms \
        --use_stopwords \
    --stopwords_path stop_word.txt
```
import json

def find_answer_positions(paragraph_text, answer_text):
    start_pos = paragraph_text.find(answer_text)
    if start_pos == -1:
        return None, None
    end_pos = start_pos + len(answer_text)
    return start_pos, end_pos

def process_qa_dataset(questions_file, paragraphs_file):
    # 讀取問題數據
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
    except FileNotFoundError:
        print(f"找不到問題檔案: {questions_file}")
        return None
    except json.JSONDecodeError:
        print(f"JSON 解析錯誤: {questions_file}")
        return None

    # 讀取段落數據
    try:
        with open(paragraphs_file, 'r', encoding='utf-8') as f:
            paragraphs_data = json.load(f)
    except FileNotFoundError:
        print(f"找不到段落檔案: {paragraphs_file}")
        return None
    except json.JSONDecodeError:
        print(f"JSON 解析錯誤: {paragraphs_file}")
        return None

    # 更新問題數據中的起始位置
    modified = False
    for question in questions_data['questions']:
        paragraph_id = str(question['paragraph_id'])
        paragraph_text = paragraphs_data[paragraph_id]
        
        # 找到答案的實際位置
        start, end = find_answer_positions(paragraph_text, question['answer_text'])
        
        if start is None:
            # 找不到答案時，將位置設為空值並標記為已修改
            if question.get('answer_start') is not None or question.get('answer_end') is not None:
                question['answer_start'] = None
                question['answer_end'] = None
                modified = True
                print(f"\nQuestion ID: {question['id']}")
                print(f"Warning: 找不到答案文本: {question['answer_text']}")
                print("已將 answer_start 和 answer_end 設為 None")
        elif start != question.get('answer_start') or end != question.get('answer_end'):
            # 找到新的位置時更新
            question['answer_start'] = start
            question['answer_end'] = end
            modified = True
            print(f"\nQuestion ID: {question['id']}")
            print(f"Answer text: {question['answer_text']}")
            print(f"Updated positions: {start} to {end}")
            print(f"Verification - found text: {paragraph_text[start:end]}")

    # 如果有更新，寫回文件
    if modified:
        try:
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, ensure_ascii=False, indent=2)
            print(f"\n已更新問題檔案: {questions_file}")
        except Exception as e:
            print(f"\n寫入文件時發生錯誤: {e}")
    else:
        print("\n所有位置資訊都是正確的，無需更新")

    return questions_data['questions']

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("使用方式: python qa_text_indexer.py questions.json paragraphs.json")
        sys.exit(1)

    questions_file = sys.argv[1]
    paragraphs_file = sys.argv[2]
    
    processed_data = process_qa_dataset(questions_file, paragraphs_file)
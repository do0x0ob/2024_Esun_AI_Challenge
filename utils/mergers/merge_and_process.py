import json
import glob
import os

def merge_paragraph_files(start_part=14, end_part=26, input_dir="insurance_split_14-26"):
    """合併分散的段落文件"""
    merged_paragraphs = {}
    
    print(f"開始合併文件 part_{start_part} 到 part_{end_part}")
    print(f"當前工作目錄: {os.getcwd()}")
    print(f"尋找目錄: {input_dir}")
    
    # 檢查目錄是否存在
    if not os.path.exists(input_dir):
        print(f"錯誤: 目錄 {input_dir} 不存在")
        return merged_paragraphs
    
    # Read all separated files
    for part_num in range(start_part, end_part + 1):
        filename = os.path.join(input_dir, f"part_{part_num}.json")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                part_data = json.load(f)
                print(f"成功讀取 {filename}")
                print(f"文件內容的 keys: {list(part_data.keys())}")
                merged_paragraphs.update(part_data)
                print(f"已合併 {filename}, 當前總段落數: {len(merged_paragraphs)}")
        except FileNotFoundError:
            print(f"警告: 找不到文件 {filename}")
        except json.JSONDecodeError:
            print(f"警告: 無法解析文件 {filename}")
        except Exception as e:
            print(f"處理文件 {filename} 時發生錯誤: {str(e)}")

    print(f"合併完成，所有可用的段落ID: {list(merged_paragraphs.keys())}")
    return merged_paragraphs

def process_qa_dataset(questions_file, merged_paragraphs):
    """處理QA數據集"""
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
            print(f"成功讀取問題文件，包含 {len(questions_data.get('questions', []))} 個問題")
    except FileNotFoundError:
        print(f"找不到問題檔案: {questions_file}")
        return None
    except json.JSONDecodeError:
        print(f"JSON 解析錯誤: {questions_file}")
        return None

    # Update files and reorder 
    modified = False
    questions = questions_data if isinstance(questions_data, list) else questions_data.get('questions', [])
    
    for i, question in enumerate(questions):
        old_id = question['id']
        question['id'] = i
        if old_id != i:
            print(f"\n重新編號: {old_id} -> {i}")
            modified = True
        
        paragraph_id = str(question['paragraph_id'])
        print(f"\n處理問題 {i}:")
        print(f"段落ID: {paragraph_id}")
        print(f"答案文本: {question['answer_text']}")
        
        # check if paragraph exists
        if paragraph_id not in merged_paragraphs:
            print(f"警告: 找不到段落ID {paragraph_id} 對應的文本")
            print(f"可用的段落ID: {list(merged_paragraphs.keys())}")
            question['answer_start'] = None
            question['answer_end'] = None
            modified = True
            continue
            
        paragraph_text = merged_paragraphs[paragraph_id]
        answer_text = question['answer_text']
        
        # find actual answer index
        start = paragraph_text.find(answer_text)
        if start == -1:
            print(f"Warning: 在段落 {paragraph_id} 中找不到答案文本: {answer_text}")
            print(f"段落文本前100個字符: {paragraph_text[:100]}")
            question['answer_start'] = None
            question['answer_end'] = None
            modified = True
            continue
            
        end = start + len(answer_text)
        
        # update if needed
        if start != question.get('answer_start') or end != question.get('answer_end'):
            question['answer_start'] = start
            question['answer_end'] = end
            modified = True
            print(f"找到答案在位置: {start} 到 {end}")
            print(f"驗證找到的文本: {paragraph_text[start:end]}")

    # if updated, overwrite source file
    if modified:
        output_file = questions_file.replace('.json', '_updated.json')
        output_data = {'questions': questions} if 'questions' in questions_data else questions
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"\n已將更新後的問題保存至: {output_file}")
        except Exception as e:
            print(f"\n寫入文件時發生錯誤: {e}")
    else:
        print("\n所有位置資訊都是正確的，無需更新")

    return questions

def main():
    # merge paragraphs
    merged_paragraphs = merge_paragraph_files()
    
    # saving it
    merged_file = "merged_paragraphs.json"
    with open(merged_file, 'w', encoding='utf-8') as f:
        json.dump(merged_paragraphs, f, ensure_ascii=False, indent=2)
    print(f"\n已保存合併後的段落文件: {merged_file}")
    
    # process specific question file
    question_file = "insurance_question_2.json"
    print(f"\n處理問題檔案: {question_file}")
    process_qa_dataset(question_file, merged_paragraphs)

if __name__ == '__main__':
    main()
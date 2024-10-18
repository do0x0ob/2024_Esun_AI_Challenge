import json
import os
import argparse

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def compare_answers(output_path, ground_truth_path):
    output = load_json(output_path)
    ground_truth = load_json(ground_truth_path)

    correct_count = 0
    total_count = len(ground_truth['ground_truths'])
    incorrect_questions = []

    for output_answer in output['answers']:
        qid = output_answer['qid']
        retrieve = output_answer['retrieve']

        gt_answer = next((item for item in ground_truth['ground_truths'] if item['qid'] == qid), None)

        if gt_answer and gt_answer['retrieve'] == retrieve:
            correct_count += 1
        else:
            incorrect_questions.append({
                'qid': qid,
                'output_retrieve': retrieve,
                'ground_truth_retrieve': gt_answer['retrieve'] if gt_answer else 'Not found',
                'category': gt_answer['category'] if gt_answer else 'Unknown'
            })

    accuracy = correct_count / total_count if total_count > 0 else 0

    print(f"Correct answers: {correct_count}")
    print(f"Total questions: {total_count}")
    print(f"Accuracy: {accuracy:.2%}")

    print("\nIncorrect questions:")
    for q in incorrect_questions:
        print(f"QID: {q['qid']}, Output: {q['output_retrieve']}, Correct answer: {q['ground_truth_retrieve']}, Category: {q['category']}")

def main():
    parser = argparse.ArgumentParser(description="Compare output answers with ground truth.")
    parser.add_argument("--data_dir", required=True, help="Path to the directory containing the dataset")
    args = parser.parse_args()

    # Set file paths
    output_path = os.path.join(os.getcwd(), 'output_answers.json')
    ground_truth_path = os.path.join(args.data_dir, 'dataset', 'preliminary', 'ground_truths_example.json')

    # Check if files exist
    if not os.path.exists(output_path):
        print(f"Error: {output_path} does not exist.")
        return
    if not os.path.exists(ground_truth_path):
        print(f"Error: {ground_truth_path} does not exist.")
        return

    # Run comparison
    compare_answers(output_path, ground_truth_path)

if __name__ == "__main__":
    main()
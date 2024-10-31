import os
import json
import argparse
from tqdm import tqdm
import jieba
import pdfplumber
from rank_bm25 import BM25Okapi
import itertools

class BM25Tuner:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.output_path = os.path.join(os.getcwd(), 'output_answers.json')
        self.best_params = None
        self.best_accuracy = 0
        self.results = []
        
        print("Loading all data...")
        self.load_all_data()
        print("Data loading completed!")

    def check_file_exists(self, file_path, description):
        """Check if file exists and provide detailed error message"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{description} not found at: {file_path}\n"
                                  f"Current working directory: {os.getcwd()}\n"
                                  f"Data directory: {self.data_dir}")
        return True

    def load_all_data(self):
        """Load and preprocess all required data"""
        # Set paths
        reference_path = os.path.join(self.data_dir, 'reference')
        dataset_path = os.path.join(self.data_dir, 'dataset', 'preliminary')
        
        print(f"Reference path: {reference_path}")
        print(f"Dataset path: {dataset_path}")
        
        # Check directories
        self.check_file_exists(reference_path, "Reference directory")
        self.check_file_exists(dataset_path, "Dataset directory")
        
        # Load insurance data
        print("Loading insurance PDFs...")
        self.source_path_insurance = os.path.join(reference_path, 'insurance')
        self.check_file_exists(self.source_path_insurance, "Insurance directory")
        self.corpus_dict_insurance = self.load_pdf_data(self.source_path_insurance)

        # Load finance data
        print("Loading finance PDFs...")
        self.source_path_finance = os.path.join(reference_path, 'finance')
        self.check_file_exists(self.source_path_finance, "Finance directory")
        self.corpus_dict_finance = self.load_pdf_data(self.source_path_finance)

        # Load FAQ data
        print("Loading FAQ data...")
        faq_path = os.path.join(reference_path, 'faq', 'pid_map_content.json')
        self.check_file_exists(faq_path, "FAQ file")
        with open(faq_path, 'rb') as f_s:
            self.key_to_source_dict = json.load(f_s)
            self.key_to_source_dict = {int(key): value for key, value in self.key_to_source_dict.items()}

        # Load questions and ground truth
        print("Loading questions and ground truth...")
        questions_path = os.path.join(dataset_path, 'questions_example.json')
        ground_truth_path = os.path.join(dataset_path, 'ground_truths_example.json')
        
        print(f"Questions path: {questions_path}")
        print(f"Ground truth path: {ground_truth_path}")
        
        self.check_file_exists(questions_path, "Questions file")
        self.check_file_exists(ground_truth_path, "Ground truth file")
                
        with open(questions_path, 'rb') as f:
            self.questions = json.load(f)
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)

        # Initialize tokenized corpus
        print("Preprocessing documents...")
        self.tokenized_corpus = {
            'insurance': {},
            'finance': {},
            'faq': {}
        }
        
        # Tokenize documents
        print("Tokenizing insurance documents...")
        for doc_id, content in self.corpus_dict_insurance.items():
            self.tokenized_corpus['insurance'][doc_id] = list(jieba.cut_for_search(content))
        
        print("Tokenizing finance documents...")
        for doc_id, content in self.corpus_dict_finance.items():
            self.tokenized_corpus['finance'][doc_id] = list(jieba.cut_for_search(content))
            
        print("Tokenizing FAQ documents...")
        for doc_id, content in self.key_to_source_dict.items():
            self.tokenized_corpus['faq'][doc_id] = list(jieba.cut_for_search(str(content)))

    def load_pdf_data(self, source_path):
            """Load PDF documents from source directory"""
            try:
                masked_file_ls = os.listdir(source_path)
                corpus_dict = {
                    int(file.replace('.pdf', '')): self.read_pdf(os.path.join(source_path, file)) 
                    for file in tqdm(masked_file_ls, desc=f"Loading {os.path.basename(source_path)} PDFs")
                }
                return corpus_dict
            except Exception as e:
                raise Exception(f"Error loading PDF files from {source_path}: {str(e)}")

    def read_pdf(self, pdf_loc, page_infos: list = None):
        """Extract text from PDF file"""
        try:
            with pdfplumber.open(pdf_loc) as pdf:
                pages = pdf.pages[page_infos[0]:page_infos[1]] if page_infos else pdf.pages
                pdf_text = ''
                for page in pages:
                    text = page.extract_text()
                    if text:
                        pdf_text += text
            return pdf_text
        except Exception as e:
            raise Exception(f"Error reading PDF file {pdf_loc}: {str(e)}")

    def BM25_retrieve(self, qs, source, category, k1=1.5, b=0.75, n=1):
        """Retrieve documents using BM25 algorithm"""
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
        query_tokens = list(jieba.cut_for_search(qs))
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

    def evaluate_parameters(self, params):
        """Evaluate performance for given parameter set"""
        answer_dict = {"answers": []}
        
        for q_dict in self.questions['questions']:
            retrieved = self.BM25_retrieve(
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

        # Save all results
        with open('parameter_search_results.json', 'w', encoding='utf8') as f:
            json.dump({
                'best_params': self.best_params,
                'best_accuracy': self.best_accuracy,
                'all_results': self.results
            }, f, ensure_ascii=False, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Tune BM25 parameters")
    parser.add_argument("--data_dir", required=True, help="Path to the directory containing the dataset")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
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

    tuner = BM25Tuner(args.data_dir)
    tuner.grid_search(param_grid)

if __name__ == "__main__":
    main()
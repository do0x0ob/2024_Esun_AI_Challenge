## 當前最佳成績
**這是 Baseline 代碼跑出來的結果，我們需要至少超越它：**

Correct answers: **107** 

Total questions: **150** 

Accuracy: **71.33**%


## 首次運行流程
1. 將 repo 裡的 main branch clone 到本機 

2. 終端機進入專案文件夾下：
    - 起一個 python 虛擬環境，或是自己有環境也可以直接使用
    - 安裝一下依賴項 `pip install -r requirements.txt` 

3. 終端機輸入運行命令， 請確認一下路徑是否正確，自行依照情況組裝一下命令
    - **運行指令：** (注意 WINDOWS 的路徑是反斜線，需要自己改一下)

        `python bm25_retrieve.py --question_path <你存放競賽資料集的路徑>/競賽資料集/dataset/preliminary/questions_example.json --source_path <你存放競賽資料集的路徑>/競賽資料集/reference --output_path ./output_answers.json`

    - **我的範例供參考：** 

        `python bm25_retrieve.py --question_path /Users/harperdelaviga/競賽資料集/dataset/preliminary/questions_example.json --source_path /Users/harperdelaviga/競賽資料集/reference --output_path ./output_answers.json` 

4. Baseline 程式會開始運行，大概需要執行 5 - 10 分鐘左右，運行完成後專案資料夾下會多出一個 `output_answers.json` 文檔 

5. 我加上了一隻對答案程式，運行之後會輸出正確率和錯誤的題目，方便我們量化當前結果：
    - **執行對答案程式：** `python answer_checker.py --data_dir <你存放競賽資料集的路徑>/競賽資料集`

    - **完整指令範例：** `python answer_checker.py --data_dir /Users/harperdelaviga/競賽資料集`


## 代碼庫協作方法(暫定，可再討論)
1. 每位同學創建一個或多個分支(因應採用的技術不同)，分支名稱開頭統一取一個可以辨識的名稱，例如: `YY/BM25/1`, `YY/BM25/2`，方便辨識分支是哪位同學的
2. 每次開始試新方法之前請拉取一下主幹的最新代碼，從最新版的開始改、避免策略耦合或是代碼覆蓋問題
3. 修改好的版本在本機上面先跑，如果測試結果優於當前 README 裡面的最佳成績:
    - 請修改一下本地分支 README 裡的結果為最新的
    - `Commit` 的時候記得寫一下是改動了什麼地方，方便之後回溯
    - 把變更推到遠程分支，然後可以在 line 群裡講一下
4. 有空的人可以去 clone 該分支的代碼下來跑，確認成績沒有問題
5. 確認該方案為當前最佳解之後，我會將分支代碼合到主幹去，回到步驟 2 繼續開發

## 終端運行圖片供參考
1. Baseline 運行中
   ![image](https://github.com/user-attachments/assets/add5619e-167c-404b-9ef2-dc133e6302b4)
 
2. 對答案輸出結果
   ![image](https://github.com/user-attachments/assets/b57451f3-527e-4374-b5e8-0a92e21bdf77)


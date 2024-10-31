import jieba
import os

def test_modes(text, mode_name="默認模式", with_dict=True):
    """測試不同模式的分詞"""
    print(f"\n{mode_name} ({'使用自定義詞典' if with_dict else '未使用自定義詞典'}):")
    
    if mode_name == "全模式":
        seg_list = jieba.cut(text, cut_all=True)
    elif mode_name == "精確模式":
        seg_list = jieba.cut(text, cut_all=False)
    elif mode_name == "搜索引擎模式":
        seg_list = jieba.cut_for_search(text)
    
    print("/ ".join(seg_list))

def main():
    # 測試文本
    test_texts = [
        "投資型保單的年化報酬率",
        "保險契約的要保人可以申請保單借款",
        "理財型保險商品的投資績效報告",
        "保單價值準備金與解約金的計算方式",
        "投資組合的資產配置策略"
    ]

    # 先測試未載入詞典的結果
    print("\n=== 未載入自定義詞典的分詞結果 ===")
    for text in test_texts:
        print("\n" + "="*50)
        print(f"測試文本: {text}")
        test_modes(text, "全模式", False)
        test_modes(text, "精確模式", False)
        test_modes(text, "搜索引擎模式", False)

    # 載入自定義詞典
    dict_path = "custom_dict.txt"
    if os.path.exists(dict_path):
        jieba.load_userdict(dict_path)
        print(f"\n成功載入自定義詞典: {dict_path}")
    else:
        print("\n警告: 找不到自定義詞典文件")

    # 測試載入詞典後的結果
    print("\n=== 載入自定義詞典後的分詞結果 ===")
    for text in test_texts:
        print("\n" + "="*50)
        print(f"測試文本: {text}")
        test_modes(text, "全模式", True)
        test_modes(text, "精確模式", True)
        test_modes(text, "搜索引擎模式", True)

if __name__ == "__main__":
    main()
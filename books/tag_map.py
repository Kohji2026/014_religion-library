# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf"]
# ///

"""
タグ・テーマ辞書（人が直接編集する正本）
実行すると books/data/books_index.js を生成する

実行方法:
  uv run tag_map.py

【TAG_RANGES について】
- from_page / to_page は 1始まりの連番（extract_books.py の page フィールドと対応）
- tags は religion_data.json の宗教名と一致させること（疎結合で名前一致）
- chapter は表示用ラベル（自由記述）
- 境界が不明確な箇所は ★ コメントで注記。浩二さんが目視確認後に修正してください

【THEMES について】
- 8テーマ × 主要宗教の粗いマッピング（完璧を目指さない）
- (book_key, page_no, "見出し") の形式
- page_no は 1始まりの連番
"""

# =====================================================================
# 書籍ページ → 宗教タグの対応（章単位）
# =====================================================================

TAG_RANGES = {

    # ------------------------------------------------------------------
    # godai: 図解 世界五大宗教全史（58見開き）
    # Part I 仏教 → Part 2 キリスト教 → Part 3 イスラム教
    # → Part 4 ユダヤ教 → Part 5 ヒンドゥー教
    # ★ p011-p019 の仏教後半は「Part」ラベルがOCRで取れなかったため
    #    前後の本文内容から推定。ヒンドゥー教の直前まで仏教と判断。
    # ------------------------------------------------------------------
    "godai": [
        {"from_page": 1,  "to_page": 3,  "tags": [],            "chapter": "表紙・目次・はじめに"},
        {"from_page": 4,  "to_page": 19, "tags": ["仏教"],       "chapter": "Part I 仏教"},
        {"from_page": 20, "to_page": 32, "tags": ["キリスト教"], "chapter": "Part 2 キリスト教"},
        {"from_page": 33, "to_page": 40, "tags": ["イスラム教"], "chapter": "Part 3 イスラム教"},
        {"from_page": 41, "to_page": 46, "tags": ["ユダヤ教"],   "chapter": "Part 4 ユダヤ教"},
        {"from_page": 47, "to_page": 53, "tags": ["ヒンドゥー教"], "chapter": "Part 5 ヒンドゥー教"},
        {"from_page": 54, "to_page": 56, "tags": [],            "chapter": "付録（シク教・道教・神道など）"},
        {"from_page": 57, "to_page": 58, "tags": [],            "chapter": "奥付"},
    ],

    # ------------------------------------------------------------------
    # sekai: 宗教と世界（90見開き）
    # Chapter 1 宗教概論 → ユダヤ教 → キリスト教 → イスラム教
    # → 仏教 → 神道 → 道教 → 儒教
    # ★ 各章の終了ページは次章の開始から逆算。p076〜の神道・道教・儒教は
    #    ページ数が少ないため「その他」でまとめてもよい。
    # ------------------------------------------------------------------
    "sekai": [
        {"from_page": 1,  "to_page": 17, "tags": [],              "chapter": "Chapter 1 宗教の概論"},
        {"from_page": 18, "to_page": 19, "tags": [],              "chapter": "5大宗教比較"},
        {"from_page": 20, "to_page": 24, "tags": ["ユダヤ教"],    "chapter": "Key 1 ユダヤ教"},
        {"from_page": 25, "to_page": 35, "tags": ["キリスト教"],  "chapter": "Key 2 キリスト教"},
        {"from_page": 36, "to_page": 45, "tags": ["イスラム教"],  "chapter": "Key 3 イスラム教"},
        {"from_page": 46, "to_page": 75, "tags": ["仏教"],        "chapter": "Key 4 仏教・ヒンドゥー教"},  # ★ ヒンドゥー教も含む可能性あり
        {"from_page": 76, "to_page": 82, "tags": ["神道"],        "chapter": "神道"},
        {"from_page": 83, "to_page": 86, "tags": [],              "chapter": "道教"},
        {"from_page": 87, "to_page": 90, "tags": [],              "chapter": "儒教"},
    ],

    # ------------------------------------------------------------------
    # nemure: 眠れなくなるほど面白い 図解 世界の宗教（66見開き）
    # 第1章 キリスト教 / 第2章 イスラム教 / 第3章 仏教
    # 第4章 神道 / 第5章 世界のそのほかの宗教
    # ★ 第5章の対象宗教（ヒンドゥー教・ユダヤ教等）は目次から要確認。
    # ------------------------------------------------------------------
    "nemure": [
        {"from_page": 1,  "to_page": 3,  "tags": [],              "chapter": "表紙・はじめに"},
        {"from_page": 4,  "to_page": 7,  "tags": [],              "chapter": "もくじ・プロローグ"},
        {"from_page": 8,  "to_page": 18, "tags": ["キリスト教"],  "chapter": "第1章 キリスト教"},
        {"from_page": 19, "to_page": 29, "tags": ["イスラム教"],  "chapter": "第2章 イスラム教"},
        {"from_page": 30, "to_page": 43, "tags": ["仏教"],        "chapter": "第3章 仏教"},
        {"from_page": 44, "to_page": 49, "tags": ["神道"],        "chapter": "第4章 神道"},
        {"from_page": 50, "to_page": 50, "tags": [],              "chapter": "第5章 世界のそのほかの宗教（章扉）"},
        {"from_page": 51, "to_page": 66, "tags": ["ヒンドゥー教","ユダヤ教","シーク教","儒教","ジャイナ教","ゾロアスター教","バハーイ教"], "chapter": "第5章 世界のそのほかの宗教"},
    ],

    # ------------------------------------------------------------------
    # allcolor: オールカラーでわかりやすい！世界の宗教（130見開き）
    # 第1章 宗教の基礎知識 → 第2章? キリスト教 → イスラム教
    # → 仏教 → ヒンドゥー教 → ユダヤ教 → その他
    # ★ p006に宗教一覧表があり「イスラム教」が先頭にOCRで出るが
    #    実際のイスラム教章はp037から（p036はCOLUMN扉）。
    # ------------------------------------------------------------------
    "allcolor": [
        {"from_page": 1,  "to_page": 18, "tags": [],              "chapter": "第1章 宗教の基礎知識"},
        {"from_page": 19, "to_page": 36, "tags": ["キリスト教"],  "chapter": "第2章? キリスト教"},
        {"from_page": 37, "to_page": 52, "tags": ["イスラム教"],  "chapter": "第3章? イスラム教"},
        {"from_page": 53, "to_page": 68, "tags": ["仏教"],        "chapter": "第4章? 仏教"},
        {"from_page": 69, "to_page": 78, "tags": ["ヒンドゥー教"], "chapter": "第5章? ヒンドゥー教"},
        {"from_page": 79,  "to_page": 88,  "tags": ["ユダヤ教"],    "chapter": "第6章? ユダヤ教"},
        {"from_page": 89,  "to_page": 89,  "tags": [],              "chapter": "その他の宗教（章扉）"},
        {"from_page": 90,  "to_page": 92,  "tags": ["ジャイナ教"],  "chapter": "ジャイナ教"},
        {"from_page": 93,  "to_page": 95,  "tags": ["シーク教"],    "chapter": "シーク教"},
        {"from_page": 96,  "to_page": 98,  "tags": ["ゾロアスター教"], "chapter": "ゾロアスター教"},
        {"from_page": 99,  "to_page": 101, "tags": ["儒教"],        "chapter": "儒教"},
        {"from_page": 102, "to_page": 104, "tags": ["道教"],        "chapter": "道教"},
        {"from_page": 105, "to_page": 130, "tags": [],              "chapter": "日本の宗教・索引・付録"},
    ],
}


# =====================================================================
# テーマ読み比べ（② 機能用）
# 8テーマ × 主要宗教 × 書籍 の粗いマッピング
# (book_key, page_no, "見出し") の形式
# =====================================================================

THEMES = {

    "開祖": {
        "仏教":      [("godai",   5,  "仏教の変遷①釈迦"),
                      ("sekai",  48,  "ゴータマ・シッダールタ"),
                      ("nemure", 30,  "第3章 仏教"),
                      ("allcolor",54, "悩み多き王子が仏教の開祖")],
        "キリスト教": [("godai",  20, "イエスとキリスト教の信仰の始まり"),
                      ("sekai",  25,  "現代世界で最も信徒数が多いキリスト教"),
                      ("nemure",  9,  "イエスの活動と生涯"),
                      ("allcolor",22, "イエスの生涯と代表的な逸話")],
        "イスラム教": [("godai",  34, "預言者ムハンマドの生涯①"),
                      ("sekai",  36,  "イスラム教の開祖ムハンマド"),
                      ("nemure", 19,  "第2章 イスラム教"),
                      ("allcolor",39, "預言者ムハンマドが神の啓示を受ける")],
        "ユダヤ教":  [("godai",  41,  "ユダヤ人の呼び名と歴史"),
                      ("sekai",  21,  "モーセが十戒を授かる")],
        "ヒンドゥー教": [("godai", 47, "インドの宗教史・バラモン教")],
    },

    "聖典": {
        "仏教":      [("sekai",  47,  "お経(教典)はどのようにして成立したの?"),
                      ("allcolor",57, "仏教の経典はブッダの真意")],
        "キリスト教": [("godai",  22, "聖書(Bible)"),
                      ("sekai",  27,  "新約聖書成立まで"),
                      ("nemure", 12,  "旧約聖書と新約聖書はどう違うの?"),
                      ("allcolor",28, "旧約聖書は歴史・律法・預言の書")],
        "イスラム教": [("sekai",  38,  "コーラン・六信五行"),
                      ("allcolor",46, "六信五行とは何?")],
        "ユダヤ教":  [("godai",  22,  "ユダヤ教の聖書「タナハ」"),
                      ("sekai",  23,  "トーラーの教え")],
    },

    "死生観": {
        "仏教":      [("godai",   7,  "救いのシステム・輪廻"),
                      ("sekai",  46,  "東洋宗教の死生観 輪廻と解脱")],
        "キリスト教": [("sekai",  19,  "西洋宗教の死生観 天国と地獄"),
                      ("nemure", 11,  "三位一体はキリスト教の教義")],
        "イスラム教": [("sekai",  19,  "西洋宗教の死生観（イスラム教）")],
        "ヒンドゥー教": [("godai", 48, "救いのシステム・輪廻の思想"),
                         ("allcolor",69, "ヒンドゥー教 世界で一番古い宗教?")],
    },

    "戒律": {
        "仏教":      [("nemure", 42,  "仏教の信者が守るべき「戒」には何がある?")],
        "キリスト教": [("allcolor",32, "7つの秘蹟")],
        "イスラム教": [("godai",  40,  "イスラム教の救いのシステム・五行"),
                      ("nemure", 22,  "第2章 イスラム教"),
                      ("allcolor",49, "イスラム社会でのふるまい")],
        "ユダヤ教":  [("sekai",  24,  "知っておきたいユダヤ教の食と習慣"),
                      ("godai",  46,  "ユダヤ教の救いのシステム・戒律")],
    },

    "食のタブー": {
        "イスラム教": [("sekai",  39,  "六信五行とハラールの中身"),
                      ("allcolor",50, "イスラム教 結婚と葬儀")],
        "ユダヤ教":  [("sekai",  24,  "牛肉はOK、チーズバーガーはNG!?")],
        "ヒンドゥー教": [("allcolor",69, "ヒンドゥー教")],
    },

    "儀式・祭り": {
        "仏教":      [("nemure", 41,  "仏教の各宗派はどのようにして興った?")],
        "キリスト教": [("allcolor",33, "キリスト教の春のお祭り"),
                      ("allcolor",34, "クリスマスの行事")],
        "イスラム教": [("allcolor",49, "イスラム教徒の礼拝")],
        "神道":      [("nemure", 44,  "第4章 神道")],
    },

    "結婚": {
        "イスラム教": [("allcolor",50, "特色ある結婚と葬儀")],
        "ユダヤ教":  [("sekai",  24,  "ユダヤ教の習慣")],
    },

    "歴史・分裂": {
        "仏教":      [("godai",   5,  "仏教の変遷・初期仏教〜大乗"),
                      ("sekai",  50,  "上座部仏教と大乗仏教の違い"),
                      ("nemure", 38,  "仏教はどのようにして広まっていったの?")],
        "キリスト教": [("godai",  26,  "キリスト教会の分離の歴史"),
                      ("sekai",  32,  "宗教改革とプロテスタント誕生"),
                      ("nemure", 13,  "ローマ帝国の国教となったあと"),
                      ("allcolor",26, "ルターの教え・宗教改革")],
        "イスラム教": [("godai",  36,  "正統カリフ時代"),
                      ("sekai",  42,  "カリフ？イマーム？二教派の違い"),
                      ("allcolor",40, "イスラム帝国の爆発的な発展")],
        "ユダヤ教":  [("godai",  43,  "古代イスラエルの歴史"),
                      ("sekai",  22,  "逆境Ⅱ・神殿破壊"),
                      ("allcolor",79, "ユダヤ人のための一神教")],
    },
}


# =====================================================================
# books_index.js を生成
# =====================================================================

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HISTORY_TOOL_PATH = "../009_歴史検索/index.html"


def build_tag_ranges_index():
    """宗教名 → [{book, from_page, to_page, chapter}] の逆引き辞書を生成"""
    index = {}
    for book_key, ranges in TAG_RANGES.items():
        for r in ranges:
            for tag in r["tags"]:
                if tag not in index:
                    index[tag] = []
                index[tag].append({
                    "book": book_key,
                    "from_page": r["from_page"],
                    "to_page": r["to_page"],
                    "chapter": r["chapter"],
                })
    return index


def main():
    tag_ranges_index = build_tag_ranges_index()

    data = {
        "keys": ["godai", "sekai", "nemure", "allcolor"],
        "tagRanges": tag_ranges_index,
        "themes": THEMES,
        "historyToolPath": HISTORY_TOOL_PATH,
    }

    body = ("// 自動生成: tag_map.py（手編集しない。編集は tag_map.py 本体で）\n"
            "const BOOKS_INDEX = " +
            json.dumps(data, ensure_ascii=False, indent=1) + ";\n")

    out_path = DATA_DIR / "books_index.js"
    tmp_path = out_path.with_suffix(".tmp")
    tmp_path.write_text(body, encoding="utf-8")
    tmp_path.replace(out_path)

    print(f"✅ books_index.js を生成しました: {out_path}")
    print(f"   宗教タグ数: {len(tag_ranges_index)} 宗教")
    print(f"   テーマ数:   {len(THEMES)} テーマ")
    for rel, entries in tag_ranges_index.items():
        print(f"   {rel}: {len(entries)} 章({', '.join(e['book'] for e in entries)})")


if __name__ == "__main__":
    main()

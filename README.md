# bootcamp01

## 📌 概要

`bootcamp01` は、学習用ブートキャンプ演練リポジトリです。  
主に Shell スクリプト、Kong プラグイン、Konnect データプレーン操作の練習を目的としています。

主な学習対象：
- Shell スクリプト基礎
- Kong プラグイン開発
- Konnect データプレーン操作
- テスト自動化（簡易演練）

---

## 📂 ディレクトリサリアル

```
.
├── .github/workflows/   # GitHub Actions ワークフロー
├── docs/                # ドキュメント（学習メモや規劃書）
├── kong-plugins/        # Kong プラグイン演練
├── konnect-dp/          # Konnect データプレーン操作演練
├── tests/               # テストスクリプト
├── .spectral.yaml       # Lint / スタイルガイド設定
└── README.md            # このファイル
```

---

## 🚀 開発・演習の始め方

### 前提条件

- Bash / Shell 実行環境
- Kong / Konnect 環境（演習用）
- Git

### リポジトリクローン

```bash
git clone https://github.com/mitsuru326/bootcamp01.git
cd bootcamp01
```

### 演習の実行例

各ディレクトリ内のスクリプトを Shell で実行可能です：

```bash
# tests 配付のスクリプト実行例
bash tests/sample-test.sh
```

Kong / Konnect 操作演習については、公式ドキュメントや各スクリプトのコメントを参照してください。

---

## 🛠 学習内容 / モジュール

- `kong-plugins/`：Kong プラグイン開発演習
- `konnect-dp/`：Konnect データプレーン操作演習
- `tests/`：学習用テストスクリプト
- `docs/`：学習メモやドキュメント

---

## 🤝 貢献

- Issue を立てる
- ブランチを作成 (`feature/xxx`)
- プルリクエストで提出
- 簡単なレビュー後マージ

---

## 📄 ライセンス

MIT License（必要に応じて変更してください）

---

## 📞 作者

- GitHub: [mitsuru326](https://github.com/mitsuru326)

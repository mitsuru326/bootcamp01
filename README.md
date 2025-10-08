# bootcamp01

## 📌 概要

`bootcamp01` は、ケーススタディにおけるTIS太田の解答例の資材をまとめたリポジトリである。

---

## 前提

```
### 環境
Kubernetes：AKS
コンテナレジストリ：ACR
ワークフロー：GitHub Actions

### GitHub Secretsの登録
AZURE_CREDENTIALS
DOCKERHUB_TOKEN
DOCKERHUB_USERNAME
GHCR_REGISTRY
GHCR_TOKEN
GHCR_USERNAME
KONNECT_TOKEN
REGISTRY_PASSWORD
REGISTRY_USERNAME

### GitHub Variablesの登録
CONTROL_PLANE      #例）ota-test
KONNECT_REGION     #例）us
PRODUCT_NAME       #例）bootcamp01_bookinfo
TAG                #例）bookinfo

---

## 📂 ディレクトリ構成

```
.
├── .github/workflows/   # GitHub Actions ワークフロー
├── auditlog/            # Konnectの監査ログをLog Analyticsに保存するためのモジュール
├── docs/                # APIOpsドキュメント
├── kong-plugins/        # Kong プラグイン
├── konnect-dp/          # Konnect データプレーン構成のテンプレート※ワークフローでは使わない
├── tests/               # テストスクリプト
├── .spectral.yaml       # Lint / スタイルガイド設定
└── README.md            # このファイル
```

---

## 🚀 ケーススタディ

### Konnectへのログイン、ゴールデンイメージの準備

#### Konnectへのログイン
1. Konnectへのログインは「https://cloud.konghq.com」へアクセス
#### ゴールデンイメージの準備
1. Actionの「Kong image pull & Trivy scan」を実行する
1. 必要に応じて以下のパラメータを設定する
  - Docker image tag for kong/kong-gateway (e.g. 3.11 or latest)
  - Deployment environment identifier (e.g., poc, dev, stg, prd)
  - Service or application name associated with this Data Plane (e.g., bookinfo)  


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

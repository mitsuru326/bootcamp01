# Bookinfo — アプリケーションの使い方（ユーザ向け）

このドキュメントは `Bookinfo` サンプルアプリケーションの**利用方法（デプロイ方法ではなく、アプリの操作・APIの呼び出し方）**にフォーカスしてまとめたものです。

> 前提：Bookinfo アプリケーションが稼働しており、外部からアクセスできる URL（例：`http://$GATEWAY_URL` または `http://localhost:8080` のように `/productpage` に到達できる）があることを想定しています。環境によってはポートフォワードや Gateway の設定が必要です。

---

## 1. 概要（短く）

Bookinfo は 4 つのマイクロサービスで構成されたサンプルアプリケーションです：

* `productpage` — ユーザ向けのフロントエンド画面。`details` と `reviews` を呼び出してページを組み立てます。\
* `details` — 書籍の詳細情報（著者、ページ数、ISBN 等）を返します。\
* `reviews` — 書籍のレビュー本文を返し、バージョンに応じて `ratings` を呼ぶことがあります。\
* `ratings` — 各レビューに紐づく評価（星）を返します。

（参考：Istio の Bookinfo 説明。）citeturn0search0

---

## 2. Web UI（productpage）の使い方

### 2.1 アクセス

ブラウザで次の URL を開きます（例）：

```
http://$GATEWAY_URL/productpage
# またはローカルでポートフォワードしている場合
http://localhost:8080/productpage
```

`productpage` は「Simple Bookstore App」風の単一の書籍ページを表示します。ページ内には：

* 書籍の説明（概要）
* Details（ISBN・ページ数など）
* Reviews（レビュー本文と星による評価）

### 2.2 UI の観察ポイント

* ページをリロード（更新）すると、`reviews` の複数バージョン（v1/v2/v3）がランダムに返る構成では、表示されるレビューの星の有無や色が変わる様子を確認できます（デフォルト設定ではラウンドロビンで切り替わります）。これによりバージョン差分の挙動を視覚的に確認できます。citeturn1search0

* `reviews` のバージョンごとの違い：

  * v1：`ratings` を呼ばない（星が表示されない）
  * v2：`ratings` を呼び、黒い星で評価を表示する
  * v3：`ratings` を呼び、赤い星で評価を表示する

---

## 3. API（サービス間／外部からの呼び出し）

ここでは、アプリケーションを構成する個別サービスの主な HTTP エンドポイントと、確認に使える `curl` 例、想定されるレスポンス例を示します。サービスは通常 `9080` ポートで HTTP を公開しています（環境によって異なるため、マニフェスト内の `containerPort` を確認してください）。

### 3.1 productpage（フロント）

* **用途**：HTML ページ（UI）の提供。
* **パス**：`GET /productpage`（例：`http://$GATEWAY_URL/productpage`）
* **curl（外部から確認）**：

```bash
curl -s "http://$GATEWAY_URL/productpage" | grep -o "<title>.*</title>"
# 期待例: <title>Simple Bookstore App</title>
```

クラスタ内から直接確認する場合（Pod から）:

```bash
kubectl exec -it "$(kubectl get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}')" -c ratings -- \
  curl -s productpage:9080/productpage | grep -o "<title>.*</title>"
```

（上記は Istio サンプルでよく使われる確認方法です）。citeturn1search0

### 3.2 details（書籍情報）

* **用途**：書籍のメタデータを JSON で返す。
* **典型的なパス**：`GET /details/<id>`（例：`/details/0` または `/details/1`）
* **curl（サービスに直接）**：

```bash
# クラスタ内部から service 名で呼ぶ例
kubectl exec -it "$(kubectl get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}')" -c ratings -- \
  curl -s http://details:9080/details/0
```

* **レスポンス例（JSON）**：

```json
{
  "id": 0,
  "author": "William Shakespeare",
  "year": 1595,
  "type": "paperback",
  "pages": 200,
  "publisher": "PublisherA",
  "language": "English",
  "ISBN-10": "1234567890",
  "ISBN-13": "123-1234567890"
}
```

（実例はチュートリアルや実装によって若干異なりますが、同等のフィールドを返す点は共通です）。citeturn1search1turn2search18

### 3.3 reviews（レビュー一覧）

* **用途**：指定書籍に対するレビュー配列を返す。バージョンにより ratings の呼び出し有無や表示が変わります。
* **パス**：`GET /reviews/<id>`（例：`/reviews/0`）
* **curl（例）**：

```bash
kubectl exec -it "$(kubectl get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}')" -c ratings -- \
  curl -s http://reviews:9080/reviews/0
```

* **期待動作**：

  * v1: レビュー本文のみ（星なし）。
  * v2/v3: 内部で `ratings` を呼び、レビューに評価（星）を付与する。UI（productpage）では v2 は黒星、v3 は赤星で表示されます。citeturn0search0turn1search0

### 3.4 ratings（評価）

* **用途**：レビューに付与される数値評価を返す（`reviews` から呼ばれる）。
* **パス**：`GET /ratings/<id>`（例：`/ratings/0`）
* **curl（例）**：

```bash
kubectl exec -it "$(kubectl get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}')" -c ratings -- \
  curl -s http://ratings:9080/ratings/0
```

* **レスポンス例（簡易）**：

```json
{"id":0,"rating":1}
```

（実装により戻り値の形は異なることがあるため、`/ratings/<id>` を直接叩いて確認してください）。

---

## 4. よくある操作・確認パターン

### 4.1 UI でバージョン差を確認する

* productpage をリロードしてレビューの星表示が `なし / 黒 / 赤` のどれかになることを確認します。
* もし常に同じ表示になる場合は、Istio の VirtualService / DestinationRule によりトラフィックが固定されている可能性があります（バージョン定義を確認してください）。citeturn1search2

### 4.2 各サービスの生データを直接確認する

* `kubectl exec` で任意の Pod に入り、上記の `curl` コマンドで `/details`, `/reviews`, `/ratings` を直接叩くと、フロントの集約結果ではなく、個々のサービス応答を確認できます。これにより、どのサービスがどのデータを返しているかを分解して調べられます。citeturn1search0

### 4.3 テスト用の固定リクエスト

* VM やローカル環境からクラスタ内のサービス名を解決してリクエストする例（`--resolve` を使った curl）を利用すると、外部からクラスタ内部ホスト名へ直接テストできます。実際のやり方は環境に依存しますが、Istio ドキュメントに例が掲載されています。citeturn1search1

---

## 5. トラブルシュートのヒント

* `productpage` が空白または 404 を返す：Gateway/VirtualService の設定や Service 名に誤りがないか確認してください。citeturn1search3
* レビューが常に同じバージョンで表示される：DestinationRule / VirtualService によりトラフィックが固定されていないか確認。
* 期待する JSON が返らない：対象サービス（details/reviews/ratings）の Pod ログを確認し、実際のレスポンスを `curl` で直接確認してください。

---

## 6. 参照（オリジナル）

* Istio: Bookinfo example — Overview / Run Bookinfo / Deploying the Bookinfo Application.citeturn0search0turn1search2

---

このドキュメントは「アプリケーションのユーザ視点での使い方」に絞って整理しています。さらに「UI のスクリーンショットを入れてほしい」「各サービスの実際のレスポンス JSON をファイルとして保存してほしい」といった要望があれば、そのまま反映します。

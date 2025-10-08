# bootcamp01

## 📌 概要

`bootcamp01` は、kong-bootcampで行ったケーススタディにおけるTIS太田の解答例の資材をまとめたリポジトリである。

---

## 前提

### 環境
```
Kubernetes：AKS
コンテナレジストリ：ACR
ワークフロー：GitHub Actions
```
### GitHub Secretsの登録
```
AZURE_CREDENTIALS
DOCKERHUB_TOKEN
DOCKERHUB_USERNAME
GHCR_REGISTRY
GHCR_TOKEN
GHCR_USERNAME
KONNECT_TOKEN
REGISTRY_PASSWORD
REGISTRY_USERNAME
```
### GitHub Variablesの登録
```
CONTROL_PLANE      #例）ota-test
KONNECT_REGION     #例）us
PRODUCT_NAME       #例）bootcamp01_bookinfo
TAG                #例）bookinfo
```
---

## 📂 ディレクトリ構成

```
.
├── .github/workflows/   # GitHub Actions ワークフロー
├── docs/                # APIOpsドキュメント
├── kong-plugins/        # Kong プラグイン
├── konnect-dp/          # Konnect データプレーン構成のテンプレート※ワークフローでは使わない
├── tests/               # テストスクリプト
├── trigger-auditlog/            # Konnectの監査ログをLog Analyticsに保存するためのモジュール
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
2. 必要に応じて以下のパラメータを設定する
  - Docker image tag for kong/kong-gateway (e.g. 3.11 or latest)
  - Deployment environment identifier (e.g., poc, dev, stg, prd)
  - Service or application name associated with this Data Plane (e.g., bookinfo)
3. Actionの「Publish image to GHCR (multi-arch mirror)」を実行する※「Kong image pull & Trivy scan」が正常終了すると自動起動する

  【処理概要】
  ```
    1. Docker Hubからベースイメージを取得する。
    2. Trivyによる脆弱性スキャン(レベルCriticalおよびHighの検出)を実施する。
    3. GHCRにイメージプッシュする。
  ```

### 可観測性のためのサービスの準備（Prometheus、Grafana）
#### Ingress Controller(Contour)の構築
1. Contourをデプロイする
```
kubectl apply -f https://projectcontour.io/quickstart/contour.yaml
kubectl get pods -n projectcontour -o wide
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.3/cert-manager.yaml
```
2. 「ingressclass-contour.yaml」を作成する
``` yaml:ingressclass-contour.yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: contour
spec:
  controller: projectcontour.io/ingress-controller
```
3. Contourを更新する
```
kubectl apply -f ingressclass-contour.yaml
```
#### Prometheus/Grafanaの構築
1. リポジトリを追加する
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```
2. values.yamlを作成する前に、Ingressで利用するドメインを環境変数に設定する
```
DOMAIN=apipfdev.net  #既存のAzureのDNSゾーンを利用
```
3. values.yamlを作成する。
```
cat <<EOF > ./prometheus-stack-values.yaml
alertmanager:
  ingress:
    enabled: true
    ingressClassName: contour
    annotations:
      cert-manager.io/issuer: prometheus-stack-kube-prom-self-signed-issuer
    hosts:
    - alertmanager.$DOMAIN
    tls:
    - secretName: alertmanager-general-tls
      hosts:
      - alertmanager.$DOMAIN
grafana:
  adminPassword: admin
  ingress:
    enabled: true
    ingressClassName: contour
    annotations:
      cert-manager.io/issuer: prometheus-stack-kube-prom-self-signed-issuer
    hosts:
    - grafana.$DOMAIN
    tls:
    - secretName: grafana-general-tls
      hosts:
      - grafana.$DOMAIN
  persistence:
    enabled: true
    type: statefulset
    accessModes:
    - ReadWriteOnce
    size: 20Gi
    finalizers:
    - kubernetes.io/pvc-protection
prometheusOperator:
  admissionWebhooks:
    certManager:
      enabled: true
prometheus:
  prometheusSpec:
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 20Gi
  ingress:
    enabled: true
    ingressClassName: contour
    annotations:
      cert-manager.io/issuer: prometheus-stack-kube-prom-self-signed-issuer
    hosts:
    - prometheus.$DOMAIN
    tls:
    - secretName: prometheus-general-tls
      hosts:
      - prometheus.$DOMAIN
EOF
```
4. デプロイする
```
helm upgrade -i -f prometheus-stack-values.yaml prometheus-stack prometheus-community/kube-prometheus-stack -n prometheus-stack --create-namespace --wait
```
5. Ingressに紐づいているグローバルIPアドレスをDNSのAレコードに登録する
6. 以下にそれぞれアクセスできるようになる
```
    Prometheus：http://prometheus.apipfdev.net/
    Grafana：http://grafana.apipfdev.net/
```
7. Grafanaは「values.yaml」でパスワードにadminを設定しており、初期ユーザはadminになるので、両方adminを指定すればログインできる

### Data Planeの起動、各作業のIaC化
1. Actionの「Deploy GHCR image to AKS (reusable)」を実行する※「Publish image to GHCR (multi-arch mirror)」が正常終了すると自動起動する

  【処理概要】
  ```
    1. Azureにログインする
    2. 鍵と証明書作成する
    3. Kong DPのyamlファイルを作成する
    4. GHCRにプッシュしたイメージとyamlファイルを元にAKSにデプロイする
  ```
2. インフラのIaCは対象外なので、PrometheusとGrafanaはIaC化しない

### 可観測性の実装（メトリクス、Konnectの監査ログ）
#### メトリクス
1. Kong DPのyamlファイルで以下を設定しているため、メトリクスは取得できる状態になっている
```
serviceMonitor:
  enabled: true
  labels:
    release: prometheus
```
2. 「http://prometheus.apipfdev.net/」にアクセスしてkongのメトリクスが表示されていることを確認する
   
<img width="953" height="365" alt="image" src="https://github.com/user-attachments/assets/fe07af66-5bed-4697-8d99-d0b5e5fb91b6" />

#### Konnectの監査ログ
1. Log Analytics ワークスペースを任意の名前で作成する（必要に応じてSentinelを有効化する）
2. 作成したLog Analytics ワークスペースのIDとキーを取得する
3. 関数アプリ（Azure Functions）を任意の名前で作成する
4. 当リポジトリにある「trigger-auditlog」を関数としてHTTPトリガーで登録する（VS Code等のローカルエディターで関数を作成してアップロードする必要がある）
5. 「関数の URL を取得」からエンドポイントのURLを取得する（ファンクションキーの値を選ぶ）
6. 「Konnectコンソール」→「Organization」→「Audit Logs Setup」→「Konnectタブ」にある「US - North America Endpoint」に取得したエンドポイントのURLを設定する
7. 「US - North America Webhook」を有効にする
8. Log Analytics ワークスペースで「KonnectAuditLog_CL」テーブルをクエリしてログ収集されていることを確認する。
   <img width="839" height="412" alt="image" src="https://github.com/user-attachments/assets/a7337054-67b7-4c65-b3e5-54503c660a44" />

### APIOpsの実装
#### Bookinfoのデプロイ
1. アプリのリポジトリを取得する
```
git clone https://github.com/imurata/bookinfo.git
```
2. Cloud ShellからACRにビルドするため、「build-services.sh」を以下に修正する
``` shell:build-services.sh
#!/bin/bash
set -ox errexit

# ルートディレクトリへ移動
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "$SCRIPTDIR/../../.."

# 必須環境変数
ACR_NAME="${BOOKINFO_HUB:?BOOKINFO_HUB must be set}"   # 例: kongbootcamp01registry
TAG="${BOOKINFO_TAG:?BOOKINFO_TAG must be set}"        # 例: 1.20.3

# 各サービスのビルド
SERVICES=("productpage" "details" "reviews" "ratings")

for svc in "${SERVICES[@]}"; do
  echo "Building $svc..."
  az acr build \
    --registry "$ACR_NAME" \
    --image "${svc}:${TAG}" \
    --file "samples/bookinfo/src/${svc}/Dockerfile" \
    "samples/bookinfo/src/${svc}"
done

# yaml 内のイメージ参照を更新（必要な場合）
if [[ "${BOOKINFO_UPDATE}" == "true" ]]; then
  find ./samples/bookinfo/platform -name "*bookinfo*.yaml" \
    -exec sed -i.bak "s#image:.*\\(\\/examples-bookinfo-.*\\):.*#image: ${ACR_NAME}.azurecr.io\\1:${TAG}#g" {} +
fi
```
3. 以下を実行する
```
export BOOKINFO_HUB=kongbootcamp01registry
export BOOKINFO_TAG=1.20.3
./bookinfo/src/build-services.sh
```
4. ビルドできたこと確認する
```
az acr repository list --name kongbootcamp01registry -o table
```
5. ビルドしたイメージをAKSにデプロイする
```
kubectl apply -f bookinfo/platform/kube/bookinfo.yaml
```
#### Konnect Dev PortalのPortalsとAPIsの作成・更新
1. Actionの「Create Dev Portal and APIs」を実行する
2. 必要に応じて以下のパラメータを設定する
  - APIs Name
  - APIs Version
  - Dev Portal Name
  - Team Name in Dev Portal
  - Team Role to add (Not Replace)
3. Dev Portalで「Portals」と「APIs」が作成されていることを確認する
    
#### OASドキュメントの作成とサービス＆ルートの作成
1. Actionの「Convert OpenAPI Spec to Kong and Deploy」を実行する
   または、docs/openapi/api-spec.yamlを更新する
2. 「Dev Portal」→「APIs」→「API Specification」が作成されていることを確認する
3. 「Gateway Services」と「Routes」が作成されていることを確認する

#### API Productドキュメントの作成・更新
1. Actionの「Upload Document for API Product to Konnect / Dev Portal」を実行する
   または、docs/product.mdを更新する
2. 「Dev Portal」→「APIs」→「Documentation」が作成されていることを確認する

### 初期ユースケースの実装
#### API(/api/v1)はAPIキーを持っている人のみ利用でき、流量制限を全体に適用（同一IPは直近30秒で100回を上限）
⇒apikeyなしでアクセス
```
$ http http://kong-bootcamp01.apipfdev.net/products
HTTP/1.1 401 Unauthorized
Connection: keep-alive
Content-Length: 96
Content-Type: application/json; charset=utf-8
Date: Wed, 08 Oct 2025 08:48:09 GMT
Server: kong/3.11.0.4-enterprise-edition
WWW-Authenticate: Key
X-Kong-Request-Id: 0acd5f2a5d93917d8c3f281291af4b1f
X-Kong-Response-Latency: 0

{
    "message": "No API key found in request",
    "request_id": "0acd5f2a5d93917d8c3f281291af4b1f"
}
```
apikeyありでアクセス1回目
```
$ http http://kong-bootcamp01.apipfdev.net/products apikey:bootcamp01-key
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 395
Content-Type: application/json
Date: Wed, 08 Oct 2025 08:50:21 GMT
RateLimit-Limit: 10000
RateLimit-Remaining: 9999
RateLimit-Reset: 9
Server: gunicorn
Via: 1.1 kong/3.11.0.4-enterprise-edition
X-Cache-Key: d5008eb116adb8baa882e4d09524920e86ec22f29d09a7821614747f2efe2d02
X-Cache-Status: Miss
X-Kong-Proxy-Latency: 1
X-Kong-Request-Id: 0b21023ee0617d24cf7672134a7f1133
X-Kong-Upstream-Latency: 7
X-RateLimit-Limit-30: 10000
X-RateLimit-Remaining-30: 9999

[
    {
        "descriptionHtml": "<a href=\"https://en.wikipedia.org/wiki/The_Comedy_of_Errors\">Wikipedia Summary</a>: The Comedy of Errors is one of <b>William Shakespeare's</b> early plays. It is his shortest and one of his most farcical comedies, with a major part of the humour coming from slapstick and mistaken identity, in addition to puns and word play.",
        "id": 0,
        "title": "The Comedy of Errors"
    }
]
```

#### CacheはGateway側で持たせたい
apikeyありでアクセス2回目
```
$ http http://kong-bootcamp01.apipfdev.net/products apikey:bootcamp01-key
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 395
Content-Type: application/json
Date: Wed, 08 Oct 2025 08:50:21 GMT
RateLimit-Limit: 10000
RateLimit-Remaining: 9999
RateLimit-Reset: 9
Server: gunicorn
Via: 1.1 kong/3.11.0.4-enterprise-edition
X-Cache-Key: d5008eb116adb8baa882e4d09524920e86ec22f29d09a7821614747f2efe2d02
**X-Cache-Status: Hit**
X-Kong-Proxy-Latency: 1
X-Kong-Request-Id: 09e97748c5fd8a371e426b2115caf402
X-Kong-Upstream-Latency: 0
X-RateLimit-Limit-30: 10000
X-RateLimit-Remaining-30: 9999
age: 75

[
    {
        "descriptionHtml": "<a href=\"https://en.wikipedia.org/wiki/The_Comedy_of_Errors\">Wikipedia Summary</a>: The Comedy of Errors is one of <b>William Shakespeare's</b> early plays. It is his shortest and one of his most farcical comedies, with a major part of the humour coming from slapstick and mistaken identity, in addition to puns and word play.",
        "id": 0,
        "title": "The Comedy of Errors"
    }
]
```
#### Data Planeは他のサービスや本番、開発で分ける
#### 性能を確認するためのダッシュボードが利用できる
#### Kongの学習コストは最小限に抑えて開発に集中したい
#### API Specをポータルで公開したい
#### このServiceにのみポリシーを適用したい（GWが管理する他のServiceにはポリシーが適用されないようにしたい)


## 📞 作者

- GitHub: [mitsuru326](https://github.com/mitsuru326)

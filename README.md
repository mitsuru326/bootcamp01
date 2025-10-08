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
    Prometheus：http://prometheus.apipfdev.net/
    Grafana：http://grafana.apipfdev.net/
7. Grafanaは「values.yaml」でパスワードにadminを設定しており、初期ユーザはadminになるので、両方adminを指定すればログインできる

## Data Planeの起動、各作業のIaC化
1. Actionの「Deploy GHCR image to AKS (reusable)」を実行する※「Publish image to GHCR (multi-arch mirror)」が正常終了すると自動起動する

  【処理概要】
  ```
    1. Azureにログインする
    2. 鍵と証明書作成する
    3. Kong DPのyamlファイルを作成する
    4. GHCRにプッシュしたイメージとyamlファイルを元にAKSにデプロイする
  ```
2. インフラのIaCは対象外なので、PrometheusとGrafanaはIaC化しない

## 可観測性の実装（メトリクス、Konnectの監査ログ）
### メトリクス
1. Kong DPのyamlファイルで以下を設定しているため、メトリクスは取得できる状態になっている
```
serviceMonitor:
  enabled: true
  labels:
    release: prometheus
```
2. 「http://prometheus.apipfdev.net/」にアクセスしてkongのメトリクスが表示されていることを確認する
<img width="953" height="365" alt="image" src="https://github.com/user-attachments/assets/fe07af66-5bed-4697-8d99-d0b5e5fb91b6" />
### Konnectの監査ログ


## APIOpsの実装

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

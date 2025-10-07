## Bookinfo サンプルアプリケーション

`bootcamp01` リポジトリでは、Istio を活用したマイクロサービスアーキテクチャの学習を目的とし、以下の構成で構築された Bookinfo アプリケーションを提供しています。

### アーキテクチャ概要

Bookinfo アプリケーションは、以下の 4 つのマイクロサービスで構成されています：

- **productpage**: 書籍の情報を表示するメインページを提供します。`details` と `reviews` サービスを呼び出して、書籍の詳細情報とレビューを取得します。
- **details**: 書籍の詳細情報（ISBN、ページ数など）を提供します。
- **reviews**: 書籍のレビューを提供します。`ratings` サービスを呼び出して、各レビューに対する評価を取得します。
- **ratings**: 書籍の評価情報を提供します。

`reviews` サービスには 3 つのバージョンが存在します：

- **v1**: `ratings` サービスを呼び出しません。
- **v2**: `ratings` サービスを呼び出し、評価を黒い星で表示します。
- **v3**: `ratings` サービスを呼び出し、評価を赤い星で表示します。

### サービスのデプロイ

以下のコマンドで、Bookinfo アプリケーションを Kubernetes クラスターにデプロイします：

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.27/samples/bookinfo/platform/kube/bookinfo.yaml
```

これにより、`productpage`、`details`、`reviews`、`ratings` の各サービスがデプロイされます。

### サービスのアクセス

アプリケーションを外部からアクセスするためには、Ingress Gateway を設定する必要があります。以下のコマンドで Gateway を作成します：

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.27/samples/bookinfo/networking/bookinfo-gateway.yaml
```

その後、以下のコマンドで Gateway の IP アドレスとポートを取得します：

```bash
export INGRESS_HOST=$(kubectl get gateway bookinfo-gateway -o jsonpath='{.status.addresses[0].value}')
export INGRESS_PORT=$(kubectl get gateway bookinfo-gateway -o jsonpath='{.spec.listeners[?(@.name=="http")].port}')
export GATEWAY_URL=$INGRESS_HOST:$INGRESS_PORT
```

ブラウザで `http://$GATEWAY_URL/productpage` にアクセスすると、Bookinfo アプリケーションのメインページが表示されます。

### サービスのバージョン管理

Istio を使用して、各サービスのバージョンを管理します。以下のコマンドで、各サービスの DestinationRule を作成します：

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.27/samples/bookinfo/networking/destination-rule-all.yaml
```

これにより、Istio が各サービスのバージョンを認識し、トラフィックのルーティングが可能になります。

### 次のステップ

- Istio を使用したトラフィック管理の学習
- サービス間の認証と認可の設定
- サービスメッシュの可観測性の向上（Prometheus、Grafana、Kiali などの導入）

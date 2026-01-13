# 👶 新生児管理チェックリスト

赤ちゃんの出生情報を入力すると、適切な新生児管理の推奨事項を表示するStreamlitアプリです。

## 機能

- 出生情報の入力（体重、初産/経産、在胎週数など）
- 体重に基づいた自動分類（極低出生体重児、超低出生体重児、低出生体重児、正常出生体重児）
- 状況に応じた管理推奨事項の表示
- 日常的なチェックリスト
- データのCSVエクスポート

## セットアップ

1. 必要なパッケージをインストール：
```bash
pip install -r requirements.txt
```

2. アプリを起動：
```bash
streamlit run streamlit_app.py
```

## Streamlit Cloudでの公開方法

1. GitHubリポジトリにこのコードをプッシュ
2. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
3. GitHubアカウントでサインイン
4. "New app"をクリック
5. リポジトリを選択
6. Main file pathに `streamlit_app.py` を指定
7. "Deploy"をクリック

## 注意事項

このアプリは医療アドバイスを提供するものではありません。実際の医療判断は必ず医師や医療専門家に相談してください。

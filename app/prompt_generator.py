def get_plan_structure(fmt_type: str) -> list[dict]:
    """
    各補助金種別に応じた作文構成テンプレートを返す
    """
    if fmt_type == "monozukuri":
        return [
            {"title": "1. 自社の現状と課題", "max_chars": 400},
            {"title": "2. 課題解決のための事業概要", "max_chars": 500},
            {"title": "3. 本事業の革新性", "max_chars": 400},
            {"title": "4. 補助金の必要性", "max_chars": 300},
            {"title": "5. 設備投資の具体内容", "max_chars": 300},
            {"title": "6. 補助事業の実施体制・スケジュール", "max_chars": 400},
            {"title": "7. 市場性・優位性・競合状況", "max_chars": 400},
            {"title": "8. 事業実施後の効果（売上・利益・波及効果）", "max_chars": 400},
            {"title": "9. 数値目標（付加価値額・賃金・最低賃金）", "max_chars": 300},
            {"title": "10. まとめ・将来展望", "max_chars": 300},
        ]
    elif fmt_type == "sogyo":
        return [
            {"title": "1. 創業の目的と背景", "max_chars": 500},
            {"title": "2. 商品・サービスの概要", "max_chars": 500},
            {"title": "3. 顧客と市場ニーズ", "max_chars": 400},
            {"title": "4. 実施体制とスケジュール", "max_chars": 400},
            {"title": "5. 売上予測と資金調達", "max_chars": 400},
            {"title": "6. 補助金の使途と成果目標", "max_chars": 400},
        ]
    else:
        return [{"title": "事業の概要", "max_chars": 1000}]

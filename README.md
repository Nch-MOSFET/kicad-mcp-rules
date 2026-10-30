# kicad-mcp-rules

Claude Code から KiCad を操作して基板を設計するときに使っている、ルール集・Claude Code のスキル・自作スクリプトです。
部報（2026 年）の記事「AIに基板を引かせてみた ―KiCad MCPで2枚設計して落ち着いた『人の仕事』―」の付録として公開しています。

## 中身

| 場所 | 内容 |
|---|---|
| [`rules/`](rules/KiCad_MCP_ルール.md) | KiCad MCP 利用ルール集。入口は [`KiCad_MCP_ルール.md`](rules/KiCad_MCP_ルール.md)。各ノートは「ルール → 手順 → 理由（過去の失敗）」の順に書いてある |
| [`skill/kicad-mcp/`](skill/kicad-mcp/SKILL.md) | Claude Code のスキル。KiCad の作業を始める前に、ルール集を読ませるための入口 |
| [`scripts/vascular_age_meter/`](scripts/vascular_age_meter) | 血管年齢測定器（RP2040-Zero、100×50 mm、2 層）で使ったスクリプト。基板の生成、配置（焼きなまし法＋配線の混み具合 RUDY）、配線（8 方向の A*）、補修、シルク整理、部品の差し替えなど |
| [`scripts/tea2025/`](scripts/tea2025) | TEA2025 ステレオアンプキット（100×50 mm、全 DIP）で使ったスクリプト。フットプリント・シンボル・回路図の生成、基板の生成、シルク整理、面付け |

スクリプトの役割の一覧は [`rules/08_スクリプト一覧.md`](rules/08_スクリプト一覧.md) にある。

## 前提の環境

- [KiCad](https://www.kicad.org/) 10（`kicad-cli` と、KiCad 付属 Python の `pcbnew`）
- [Claude Code](https://code.claude.com/docs/ja/overview)
- KiCad MCP サーバ: [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)（MIT ライセンス。このリポジトリには含めていない。v2.8.2 で使用）
- [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py)（LCSC の部品の取り込み）

## 使い方

1. KiCad MCP サーバを入れて、Claude Code に登録する（サーバの README を参照）。
2. `skill/kicad-mcp/` を `~/.claude/skills/kicad-mcp/` に置き、`SKILL.md` に書いたルール集の場所を、このリポジトリを置いた場所に書き換える。
3. Claude Code に「kicadMCPで基板を作って」のように頼むと、ルール集を読んでから作業を始める。

## 注意

- スクリプトは特定の基板のために書いた手本で、このままでは動かない（基板データやネットリストは含めていない）。中のパスは公開用に `C:/Users/<user>/...` へ書き換えてある。
- ルール集の場所や既定値（JLCPCB 推奨の設計ルール、線幅 0.5／1.0 mm など）は、筆者の環境と好みに合わせたもの。自分の環境に合わせて直して使う。
- 部品のデータシートは含めていない。各メーカーや販売店のサイトから入手すること。

## ライセンス

[MIT License](LICENSE)

# 出産手当金

- 健康保険法102条: https://laws.e-gov.go.jp/law/211AC0000000070/
- 協会けんぽ 出産手当金: https://www.kyoukaikenpo.or.jp/benefit/childbirth/001/index.html

## 支給要件（健康保険法102条・協会けんぽ公式より）
- 健康保険の被保険者であること（国保には出産手当金なし）
- 出産のため会社を休んでいること
- 妊娠4か月（85日）以降の出産
- 支給期間: 出産日前42日（多胎98日）〜出産翌日後56日
- 支給額: 標準報酬日額の2/3

## 現ルールでの判定
- ninshin=true + hoken_shubetsu=shakai_hoken を判定条件として使用
- 両条件とも健康保険法102条の要件に直接対応

source_url: https://www.kyoukaikenpo.or.jp/g6/cat620/r314/
source_quote: "出産のため会社を休み、その間に給与の支払いを受けなかった場合に支給"

# 雇用保険基本手当（失業給付）

- 雇用保険法13条（受給資格）・15条（失業の認定）: https://laws.e-gov.go.jp/law/349AC0000000116/
- ハローワーク 雇用保険の基本手当: https://www.hellowork.mhlw.go.jp/insurance/insurance_basicbenefit.html

## 支給要件（雇用保険法・ハローワーク公式より）
- 雇用保険の被保険者であったこと（離職前2年間に12か月以上、特定理由離職者は6か月以上）
- 失業の状態にあること（就職の意思・能力があり求職活動を行っている）
- ハローワークに求職の申込みを行うこと
- 待期期間7日間の経過後に支給開始
- 自己都合退職の場合は給付制限期間あり（2025年4月改正で1か月に短縮）

## 現ルールでの判定
- koyou_hoken=true（雇用保険に加入/加入していた）かつ rishoku=true（離職中）を必要条件として判定
- 被保険者期間の詳細や給付制限期間はProlog判定の範囲外（窓口確認を案内）

source_url: https://www.hellowork.mhlw.go.jp/insurance/insurance_basicbenefit.html
source_quote: "雇用保険の被保険者の方が離職し、失業中の生活を心配しないで新しい仕事を探すために支給されるもの"

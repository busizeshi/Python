# Trading Agents Package (Teaching Demo)

鏈」鐩紨绀轰簡涓€涓暀瀛︾敤鐨勪氦鏄撲唬鐞嗙郴缁燂紝鍖呭惈 **涓夌绛栫暐 Agent**锛?
- **Rule**: 绾鍒欑瓥鐣ワ紝鍩轰簬鍧囩嚎浜ゅ弶鐢熸垚 BUY / SELL 淇″彿銆?- **LLM**: 澶фā鍨嬬瓥鐣ワ紝杈撳叆 RSI 鍜屽潎绾挎寚鏍囷紝璁?LLM 鍐崇瓥 BUY / SELL / HOLD銆?- **Hybrid**: 娣峰悎绛栫暐锛岀粨鍚堣鍒欍€侀闄╂帶鍒朵笌 LLM 杈呭姪锛岄伩鍏嶆槑鏄句簭鎹熷苟鎻愬崌绋冲畾鎬с€?
---

## 瀹夎渚濊禆

鍦ㄩ」鐩牴鐩綍杩愯锛?
```bash
pip install -r requirements.txt
$env:DASHSCOPE_API_KEY="你的千问API Key"`r`n$env:LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"`r`n$env:LLM_MODEL="qwen-turbo"
```
---

## 杩愯鏂瑰紡

杩涘叆椤圭洰鐩綍鍚庯紝鍙互閫夋嫨涓嶅悓绛栫暐妯″紡锛?
### Rule 绛栫暐
```bash
python streaming_main.py --mode rule --budget 100000 --short 5 --long 20
```

### LLM 绛栫暐
```bash
python streaming_main.py --mode llm --budget 100000 --short 5 --long 20
```

### Hybrid 绛栫暐锛堟帹鑽愶級
```bash
python streaming_main.py --mode hybrid --budget 100000 --short 5 --long 20
```

---

## 鍙傛暟璇存槑
- `--mode`: 杩愯妯″紡锛屽彲閫?`rule` / `llm` / `hybrid`  
- `--budget`: 鍒濆璧勯噾 (榛樿 100000)  
- `--short`: 鐭湡鍧囩嚎绐楀彛 (榛樿 5)  
- `--long`: 闀挎湡鍧囩嚎绐楀彛 (榛樿 20)  

---

## 缁撴灉杈撳嚭
杩愯鍚庝細锛?- 鎵撳嵃姣忔棩浠锋牸銆佺煭鏈?闀挎湡鍧囩嚎銆丷SI 鍊? 
- 杈撳嚭鍐崇瓥璇存槑锛堣鍒欒В閲婃垨 LLM 杈呭姪淇″彿锛? 
- 鍦ㄧ粨鏉熸椂杈撳嚭鏈€缁堢殑鎶曡祫缁勫悎鎶ュ憡锛屽寘鎷祫閲戜綑棰濄€佹寔浠撹偂鏁般€佺粍鍚堟€讳环鍊肩瓑  

---

## 鏂囦欢缁撴瀯
```
trading_agents_package_teaching/
鈹溾攢 agents/
鈹? 鈹溾攢 strategy_agent_rule.py      # 瑙勫垯绛栫暐
鈹? 鈹溾攢 strategy_agent_llm.py       # 澶фā鍨嬬瓥鐣?鈹? 鈹溾攢 strategy_agent_hybrid.py    # 娣峰悎绛栫暐
鈹? 鈹溾攢 data_agent.py               # 鏁版嵁鍔犺浇
鈹? 鈹溾攢 eval_agent.py               # 鍥炴祴鎵ц
鈹? 鈹溾攢 report_agent.py             # 鎶ュ憡杈撳嚭
鈹溾攢 data/
鈹? 鈹斺攢 sample_prices.csv           # 绀轰緥浠锋牸鏁版嵁
鈹溾攢 streaming_main.py              # 涓荤▼搴?鈹溾攢 requirements.txt               # 渚濊禆鍒楄〃
鈹斺攢 README.md                      # 椤圭洰璇存槑
```

---

## 鎺ㄨ崘浣跨敤鏂瑰紡
寤鸿浼樺厛浣跨敤 **Hybrid 绛栫暐**锛?- 鍦ㄥ己淇″彿鏃剁敱瑙勫垯鐩存帴鍐崇瓥锛堥伩鍏?LLM 鍑洪敊锛? 
- 鍦ㄦā绯婂尯闂存椂寮曞叆 LLM 鎻愪緵杈呭姪鎰忚  
- 鍐呯疆姝㈡崯/姝㈢泩閫昏緫锛屾彁楂樿祫閲戞洸绾跨ǔ瀹氭€? 


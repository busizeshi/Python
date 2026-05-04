"""
LLM鍔╂墜妯″潡锛氭彁渚涙櫤鑳藉垽鍒嗐€佽В閲婄敓鎴愬拰瀛︿範寤鸿鍔熻兘
"""
from __future__ import annotations
import os
from typing import Any, Tuple, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from .memory import StudentProfile, SkillStat
from .questions import Question

# 鍔犺浇鐜鍙橀噺
load_dotenv()

class LLMAssistant:
    """LLM鍔╂墜绫伙紝鎻愪緵鍚勭AI澧炲己鍔熻兘"""
    
    def __init__(self):
        # OpenAI SDK 兼容模式：支持阿里千问与 OpenAI。
        # 优先顺序：
        # 1) LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
        # 2) DASHSCOPE_API_KEY（默认千问兼容 base_url + qwen-plus）
        # 3) OPENAI_API_KEY（默认 gpt-4o-mini）
        llm_api_key = os.getenv("LLM_API_KEY")
        llm_base_url = os.getenv("LLM_BASE_URL")
        llm_model = os.getenv("LLM_MODEL")

        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if llm_api_key:
            api_key = llm_api_key
            base_url = llm_base_url
            default_model = llm_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        elif dashscope_api_key:
            api_key = dashscope_api_key
            base_url = llm_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            default_model = llm_model or "qwen-plus"
        else:
            api_key = openai_api_key
            base_url = llm_base_url
            default_model = llm_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_model = default_model
        self.grading_model = os.getenv("LLM_GRADING_MODEL", self.default_model)
        self.explanation_model = os.getenv("LLM_EXPLANATION_MODEL", self.default_model)
        self.conversation_model = os.getenv("LLM_CONVERSATION_MODEL", self.default_model)
    
    def smart_grade(self, question: Question, user_answer: Any) -> Tuple[bool, str, float]:
        """
        鏅鸿兘鍒ゅ垎锛氫娇鐢↙LM瀵瑰鐢熺瓟妗堣繘琛岃涔夎瘎浼?        
        Returns:
            (is_correct, explanation, confidence): 鏄惁姝ｇ‘銆佽В閲娿€佺疆淇″害
        """
        # 瀵逛簬閫夋嫨棰橈紝浠嶄娇鐢ㄤ紶缁熷垽鍒?
        if question.options:
            is_correct = user_answer == question.answer
            explanation = self._generate_explanation(question, user_answer, is_correct)
            return is_correct, explanation, 1.0
        
        # 瀵逛簬寮€鏀鹃锛屼娇鐢↙LM杩涜璇箟鍒ゅ垎
        return self._llm_grade_open_question(question, user_answer)
    
    def _llm_grade_open_question(self, question: Question, user_answer: Any) -> Tuple[bool, str, float]:
        """浣跨敤LLM瀵瑰紑鏀鹃杩涜鍒ゅ垎"""
        prompt = f"""
浣滀负鑻辫瀛︿範鍔╂墜锛岃璇勪及瀛︾敓瀵逛互涓嬮鐩殑鍥炵瓟锛?
棰樼洰: {question.stem}
姝ｇ‘绛旀: {question.answer}
瀛︾敓绛旀: {user_answer}
棰樼洰绛夌骇: {question.cefr}
鎶€鑳芥爣绛? {', '.join(question.tags)}

璇蜂粠浠ヤ笅鍑犱釜鏂归潰璇勪及锛?1. 璇箟鍑嗙‘鎬э細瀛︾敓绛旀鏄惁琛ㄨ揪浜嗘纭殑鎰忔€?2. 璇硶姝ｇ‘鎬э細鏄惁鏈夎娉曢敊璇?3. 璇嶆眹閫傚綋鎬э細鐢ㄨ瘝鏄惁鍚堥€?
璇疯繑鍥濲SON鏍煎紡锛?{{
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "explanation": "璇︾粏瑙ｉ噴锛屽寘鎷敊璇垎鏋愬拰鏀硅繘寤鸿",
    "grammar_issues": ["璇硶闂鍒楄〃"],
    "vocabulary_suggestions": ["璇嶆眹寤鸿鍒楄〃"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.grading_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            result = json.loads(content)
            
            return (
                result.get("is_correct", False),
                result.get("explanation", ""),
                result.get("confidence", 0.5)
            )
            
        except Exception as e:
            print(f"LLM鍒ゅ垎鍑洪敊: {e}")
            # 闄嶇骇鍒扮畝鍗曞瓧绗︿覆鍖归厤
            is_correct = str(user_answer).strip().lower() == str(question.answer).strip().lower()
            return is_correct, f"绠€鍗曞尮閰嶇粨鏋溿€傛纭瓟妗? {question.answer}", 0.8 if is_correct else 0.3
    
    def _generate_explanation(self, question: Question, user_answer: Any, is_correct: bool) -> str:
        """涓洪€夋嫨棰樼敓鎴愪釜鎬у寲瑙ｉ噴"""
        if question.explain:
            base_explanation = question.explain
        else:
            base_explanation = f"姝ｇ‘绛旀鏄? {question.answer}"
        
        # 濡傛灉绛斿浜嗭紝缁欎簣榧撳姳
        if is_correct:
            return f"鉁?绛斿浜嗭紒{base_explanation}"
        
        # 濡傛灉绛旈敊浜嗭紝浣跨敤LLM鐢熸垚鏇磋缁嗙殑瑙ｉ噴
        prompt = f"""
瀛︾敓鍋氶敊浜嗚繖閬撹嫳璇锛岃鐢熸垚涓€涓湁甯姪鐨勮В閲婏細

棰樼洰: {question.stem}
閫夐」: {question.options}
姝ｇ‘绛旀: {question.answer}
瀛︾敓閫夋嫨: {user_answer}
鍩虹瑙ｉ噴: {base_explanation}
闅惧害绛夌骇: {question.cefr}

璇风敓鎴愪竴涓畝娲佷絾鏈夊府鍔╃殑瑙ｉ噴锛屽寘鎷細
1. 涓轰粈涔堝鐢熺殑閫夋嫨鏄敊璇殑
2. 姝ｇ‘绛旀鐨勫師鐞?3. 璁板繂鎶€宸ф垨瑙勫緥
4. 榧撳姳鎬х殑璇濊

鎺у埗鍦?-3鍙ヨ瘽鍐呫€?"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.explanation_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else "鉂?瑙ｉ噴鐢熸垚澶辫触"
            
        except Exception as e:
            print(f"瑙ｉ噴鐢熸垚鍑洪敊: {e}")
            return f"鉂?{base_explanation}"
    
    def generate_learning_advice(self, profile: StudentProfile) -> str:
        """鏍规嵁瀛︾敓妗ｆ鐢熸垚涓€у寲瀛︿範寤鸿"""
        # 鍒嗘瀽钖勫急鎶€鑳?        weak_skills = []
        strong_skills = []
        
        for skill, stat in profile.skills.items():
            if stat.mastery < 0.4:
                weak_skills.append((skill, stat.mastery))
            elif stat.mastery > 0.8:
                strong_skills.append((skill, stat.mastery))
        
        weak_skills.sort(key=lambda x: x[1])  # 鎸夋帉鎻″害鎺掑簭
        strong_skills.sort(key=lambda x: x[1], reverse=True)
        
        prompt = f"""
浣滀负鑻辫瀛︿範椤鹃棶锛岃涓鸿繖浣嶅鐢熺敓鎴愪釜鎬у寲瀛︿範寤鸿锛?
瀛︾敓淇℃伅锛?- 濮撳悕: {profile.name}
- 褰撳墠绛夌骇: {profile.level}
- 鎬荤瓟棰樻暟: {len(profile.history)}

钖勫急鎶€鑳?(鎺屾彙搴?< 0.4):
{chr(10).join([f"- {skill}: {mastery:.2f}" for skill, mastery in weak_skills[:5]])}

寮洪」鎶€鑳?(鎺屾彙搴?> 0.8):
{chr(10).join([f"- {skill}: {mastery:.2f}" for skill, mastery in strong_skills[:3]])}

璇风敓鎴愶細
1. 閽堝钖勫急鎶€鑳界殑鍏蜂綋瀛︿範寤鸿
2. 濡備綍鍒╃敤寮洪」鎶€鑳芥潵鎻愬崌鏁翠綋姘村钩
3. 閫傚悎褰撳墠绛夌骇鐨勫涔犵瓥鐣?4. 榧撳姳鎬х殑璇濊

淇濇寔绠€娲佹湁鐢紝鎺у埗鍦?50瀛楀唴銆?"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.conversation_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else "瀛︿範寤鸿鐢熸垚澶辫触"
            
        except Exception as e:
            print(f"瀛︿範寤鸿鐢熸垚鍑洪敊: {e}")
            return self._generate_simple_advice(weak_skills, strong_skills, profile.level)
    
    def _generate_simple_advice(self, weak_skills: List, strong_skills: List, level: str) -> str:
        """生成简单学习建议（降级方案）"""
        advice = f"基于你当前的 {level} 等级表现："
        
        if weak_skills:
            top_weak = weak_skills[0][0]
            advice += f"\n- 重点关注: {top_weak}"
        
        if strong_skills:
            top_strong = strong_skills[0][0]
            advice += f"\n- 继续保持: {top_strong}"
        
        advice += "\n- 建议多练习当前等级题目，巩固基础后再挑战更高难度。"
        
        return advice
    
    def chat_with_student(self, user_input: str, profile: StudentProfile) -> str:
        """与学生进行对话交流"""
        prompt = f"""
浣犳槸涓€涓弸濂界殑鑻辫瀛︿範鍔╂墜銆傚鐢熷悜浣犳彁闂垨浜ゆ祦銆?
瀛︾敓淇℃伅锛?- 濮撳悕: {profile.name}  
- 绛夌骇: {profile.level}
- 绛旈鍘嗗彶: {len(profile.history)}棰?
瀛︾敓璇? {user_input}

璇风敤涓枃鍥炲锛屼繚鎸佸弸濂姐€佹湁甯姪鐨勮璋冦€傚鏋滄槸鑻辫瀛︿範鐩稿叧闂锛屾彁渚涘噯纭殑瑙ｇ瓟銆?鎺у埗鍦?00瀛楀唴銆?"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.conversation_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else "抱歉，我现在无法回答这个问题。"
            
        except Exception as e:
            print(f"瀵硅瘽鐢熸垚鍑洪敊: {e}")
            return "抱歉，我现在无法回答这个问题。请继续你的学习。"

# 鍏ㄥ眬LLM鍔╂墜瀹炰緥
_llm_assistant = None

def get_llm_assistant() -> Optional[LLMAssistant]:
    """鑾峰彇LLM鍔╂墜瀹炰緥"""
    global _llm_assistant
    
    if _llm_assistant is None:
        try:
            _llm_assistant = LLMAssistant()
            # 娴嬭瘯杩炴帴
            test_response = _llm_assistant.client.chat.completions.create(
                model=_llm_assistant.default_model,
                messages=[{"role": "user", "content": "娴嬭瘯杩炴帴"}],
                max_tokens=5
            )
            print("LLM助手初始化成功")
        except Exception as e:
            print(f"LLM助手初始化失败: {e}")
            print("将使用传统判分模式")
            _llm_assistant = None
    
    return _llm_assistant

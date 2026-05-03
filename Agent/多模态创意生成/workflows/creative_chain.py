from agents.copywriter_agent import CopyWriterAgent
from agents.designer_agent import DesignerAgent
from agents.reviewer_agent import ReviewerAgent


class CreativeChain:
    def __init__(self):
        self.copywriter = CopyWriterAgent()
        self.designer = DesignerAgent()
        self.reviewer = ReviewerAgent()

    def run(self, product: str, audience: str):
        print(f"正在为产品“{product}”和受众“{audience}”生成创意广告...")

        draft_text = self.copywriter.run(product, audience)
        print("初稿文案:", draft_text)

        final_text = self.reviewer.run(draft_text)
        print("优化文案:", final_text)

        image_prompt = f"广告海报：{final_text}，清爽夏日风格，商业摄影，高质量。"
        image_path = self.designer.run(image_prompt)
        print("海报已生成:", image_path)

        return final_text, image_path

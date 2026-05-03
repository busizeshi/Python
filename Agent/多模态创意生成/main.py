import argparse
import os

from workflows.creative_chain import CreativeChain


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Creative Campaign Generator")
    parser.add_argument("--product", type=str, default="iphone 手机", help="产品名称")
    parser.add_argument("--audience", type=str, default="年轻人", help="目标受众")
    args = parser.parse_args()

    creative_chain = CreativeChain()
    text, img_path = creative_chain.run(args.product, args.audience)

    os.makedirs("outputs", exist_ok=True)
    with open("outputs/campaign.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print("文案已保存: outputs/campaign.txt")
    print(f"海报已保存: {img_path}")

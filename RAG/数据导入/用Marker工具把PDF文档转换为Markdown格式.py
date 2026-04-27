import os
import subprocess

def convert_pdf_to_markdown(input_pdf_path,output_folder,max_pages=12):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    command=[
        'marker_single',
        input_pdf_path,
        output_folder,
        f'--max_pages={max_pages}'
    ]

    try:
        subprocess.run(command,check=True)
        print(f"PDF文档转换为Markdown格式成功，文件已保存至{output_folder}文件夹")
    except subprocess.CalledProcessError as e:
        print(f"PDF文档转换失败： {e}")

if __name__ == "__main__":
    input_pdf_path = "../data/山西文旅/云冈石窟-en.pdf "
    output_folder = "../data/marker/output/云冈石窟-en"
    convert_pdf_to_markdown(input_pdf_path, output_folder)
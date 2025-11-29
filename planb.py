import re
import json

def clean_text_content(text):
    """
    深度清洗文本：去除[source]标签、页眉页脚、水印干扰词
    """
    # 1. 去除所有反斜杠
    text = text.replace('\\', '')
    
    # 2. 去除页码标记 (如 --- PAGE 1 --- 或 - 1 -)
    text = re.sub(r'---\s*PAGE\s*\d+\s*---', '', text)
    text = re.sub(r'^\s*-\s*\d+\s*-\s*$', '', text, flags=re.MULTILINE)
    
    # 3. 去除文档特有的水印干扰词
    noise_patterns = [
        "STATE GRID", "CORPORATION", "OF CHINA", "VNIH", "HINA",
        "国家电网有限公司", "高校毕业生招聘考试", "公共与行业知识题库",
        "一、单选题", "二、多选题", "三、判断题", 
        "第一部分", "第二部分", "第三部分", "第四部分", "第五部分",
        "形势政策", "企业文化", "公司战略", "新型电力系统", "品牌建设"
    ]
    for p in noise_patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
        
    # 4. 去除被打散的单字干扰
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) <= 2 and re.search(r'[国家电网公司]', stripped):
            continue
        if stripped:
            clean_lines.append(stripped)
    return '\n'.join(clean_lines)

def convert_to_json(raw_text):
    # 1. 清洗全文本
    content = clean_text_content(raw_text)
    
    # 2. 统一标点
    content = content.replace('：', ':').replace('（', '(').replace('）', ')')
    
    # 3. 利用题号切分题目
    content = re.sub(r'\n(\d+)、', r'\n<SPLIT>\1、', content)
    blocks = content.split('<SPLIT>')
    
    questions_list = []
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        id_match = re.match(r'^(\d+)、', block)
        if not id_match:
            continue
        
        q_id = int(id_match.group(1))
        
        # 提取答案（兼容多个选项、顿号、空格）
        ans_match = re.search(r'答案\s*[:：]\s*([A-D、\s]+)', block)
        if not ans_match:
            continue
        raw_ans = ans_match.group(1)
        answer = raw_ans.replace('、', '').replace(' ', '').strip()
        
        # 提取题目主体
        body_start = len(id_match.group(0))
        body_end = ans_match.start()
        full_body = block[body_start:body_end].strip()
        
        # 提取选项
        options = {}
        question_text = full_body
        first_opt_match = re.search(r'(^|\s)A[\.．]', full_body)
        if first_opt_match:
            question_text = full_body[:first_opt_match.start()].strip()
            opts_text = full_body[first_opt_match.start():]
            opts_text_flat = opts_text.replace('\n', ' ')
            opt_pattern = r'([A-D])[\.．](.*?)(?=\s[A-D][\.．]|$)'
            found_opts = re.findall(opt_pattern, opts_text_flat)
            for k, v in found_opts:
                options[k] = v.strip()
        else:
            # 判断题默认选项
            options = {"A": "正确", "B": "错误"}
        
        question_text = question_text.replace('\n', '')
        
        questions_list.append({
            "id": q_id,
            "question": question_text,
            "options": options,
            "answer": answer
        })
    
    return questions_list

if __name__ == '__main__':
    try:
        with open('input.txt', 'r', encoding='utf-8-sig') as f:
            raw_data = f.read()
        
        result = convert_to_json(raw_data)
        
        with open('output.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"成功转换 {len(result)} 道题目！结果已保存为 output.json")
        
    except FileNotFoundError:
        print("错误：请先创建 'input.txt' 文件，并将题库内容粘贴进去。")

"""รูปแบบ prompt ที่ใช้ร่วมกันระหว่างตอนเทรนและ preprocess.py

ต้องใช้ฟังก์ชันนี้ทั้งสองที่ เพื่อไม่ให้รูปแบบ prompt ตอนเทรนกับตอนเรียกโมเดลจริงไม่ตรงกัน
(ถ้าไม่ตรง โมเดลจะตอบแย่ลงมากเพราะเจอรูปแบบที่ไม่เคยเห็นตอนเทรน)
"""

SQL_MARKER = "### SQL"


def build_prompt(question: str, schema_ddl: str) -> str:
    """สร้าง prompt จากคำถามและ DDL ของ schema

    คำตอบที่คาดหวังต่อจาก "### SQL" มีได้ 3 แบบเท่านั้น: SQL, <REFUSE>, <CLARIFY>
    """
    schema_ddl = schema_ddl.strip()
    question = question.strip()
    return (
        "### Schema\n"
        f"{schema_ddl}\n"
        "\n"
        "### คำถาม\n"
        f"{question}\n"
        "\n"
        f"{SQL_MARKER}\n"
    )

# Windows (Git Bash ไม่มี make): ใช้ sh scripts/tasks.sh <คำสั่ง> แทน
.PHONY: setup data test model dev tunnel

setup data test model dev tunnel:
	sh scripts/tasks.sh $@

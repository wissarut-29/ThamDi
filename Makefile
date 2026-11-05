# Windows (Git Bash ไม่มี make): ใช้ sh scripts/tasks.sh <คำสั่ง> แทน
.PHONY: setup data test model dev funnel

setup data test model dev funnel:
	sh scripts/tasks.sh $@

run:
	@echo "" > logs/shorter.log
	python shorter.py &
	@echo "" > logs/mixer.log
	python mixer1.py &
stop:
	@ps aux | grep "python mixer.py" | grep -v grep | awk '{print $$2}' | xargs kill -9
	@ps aux | grep "python shorter.py" | grep -v grep | awk '{print $$2}' | xargs kill -9
test:
	python -m unittest -v
.PHONY: run stop test

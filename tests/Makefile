.PHONY: test test-verbose test-coverage test-matching test-integration test-database test-anti-repeat test-fast test-stress test-one install-test-deps

# Установить тестовые зависимости
install-test-deps:
	pip3 install -r test_requirements.txt --break-system-packages

# Запустить все тесты
test:
	cd .. && python3 -m pytest tests/ -v

# Запустить тесты с подробным выводом
test-verbose:
	cd .. && python3 -m pytest tests/ -v -s

# Запустить тесты с покрытием кода
test-coverage:
	cd .. && python3 -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Запустить только тесты мэтчинга
test-matching:
	cd .. && python3 -m pytest tests/test_matching.py -v

# Запустить только интеграционные тесты
test-integration:
	cd .. && python3 -m pytest tests/test_integration.py -v

# Запустить только тесты базы данных
test-database:
	cd .. && python3 -m pytest tests/test_database.py -v

# Запустить тесты анти-повтора
test-anti-repeat:
	cd .. && python3 -m pytest tests/test_matching.py::TestMatchingAntiRepeat -v

# Быстрые тесты (исключая стресс-тесты)
test-fast:
	cd .. && python3 -m pytest tests/ -v -m "not stress"

# Только стресс-тесты
test-stress:
	cd .. && python3 -m pytest tests/ -v -m "stress"

# Запустить один конкретный тест (пример)
test-one:
	cd .. && python3 -m pytest tests/test_database.py::TestDatabase::test_create_user -v -s

# Запустить тесты по ключевым словам
test-keyword:
	cd .. && python3 -m pytest tests/ -v -k "$(KEYWORD)"
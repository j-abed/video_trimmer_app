# Makefile for Video Trimmer Pro
# Provides convenient commands for development and deployment

.PHONY: help install install-dev test clean lint format run run-enhanced run-basic benchmark setup-env

# Default target
help:
	@echo "Video Trimmer Pro - Available Commands:"
	@echo "======================================="
	@echo "setup-env     - Setup development environment"
	@echo "install       - Install package and dependencies"
	@echo "install-dev   - Install with development dependencies"
	@echo "run           - Run application (auto-detect best version)"
	@echo "run-enhanced  - Run enhanced version with modern UI"
	@echo "run-basic     - Run basic version"
	@echo "test          - Run all tests"
	@echo "test-enhanced - Run enhanced feature tests"
	@echo "benchmark     - Run performance benchmarks"
	@echo "lint          - Run code linting"
	@echo "format        - Format code with black"
	@echo "clean         - Clean temporary files"
	@echo "docs          - Generate documentation"
	@echo "package       - Create distribution package"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup-env && make run"

# Environment setup
setup-env:
	@echo "Setting up development environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source venv/bin/activate  # Linux/macOS"
	@echo "  venv\\Scripts\\activate     # Windows"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Running
run:
	python launch.py

run-enhanced:
	python video_trimmer.py

run-basic:
	python video_trimmer_basic.py

# Testing
test:
	python test_video_trimmer.py
	python test_features.py

test-enhanced:
	python test_features.py

benchmark:
	python test_efficiency.py

# Code quality
lint:
	flake8 *.py --max-line-length=100 --ignore=E501,W503

format:
	black *.py --line-length=100
	isort *.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	find . -name "*.mp4" -path "./test_*" -delete
	find . -name "*.avi" -path "./test_*" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage

# Documentation
docs:
	@echo "Generating documentation..."
	@mkdir -p docs
	@echo "# Video Trimmer Documentation" > docs/README.md
	@echo "Documentation structure created in docs/"

# Packaging
package:
	python setup.py sdist bdist_wheel
	@echo "Distribution packages created in dist/"

# Docker targets (if needed)
docker-build:
	docker build -t video-trimmer-pro .

docker-run:
	docker run -it --rm -v $(PWD):/app video-trimmer-pro

# Development helpers
check-deps:
	@echo "Checking dependencies..."
	@python -c "import importlib.util; deps=['customtkinter','tkinterdnd2','moviepy','numpy','loguru','psutil']; missing=[d for d in deps if not importlib.util.find_spec(d)]; print(f'Missing: {missing}' if missing else 'All dependencies available')"

# Performance profiling
profile:
	python -m cProfile -o profile.stats video_trimmer.py
	python -c "import pstats; pstats.Stats('profile.stats').sort_stats('tottime').print_stats(20)"

# Git hooks
git-hooks:
	@echo "Setting up git hooks..."
	echo "#!/bin/bash\nmake lint" > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Git hooks installed"

# Release preparation
prepare-release:
	@echo "Preparing release..."
	make clean
	make lint
	make test
	make docs
	make package
	@echo "Release preparation complete"

# Installation verification
verify-install:
	@echo "Verifying installation..."
	@python -c "import sys; print('Python version:', sys.version.split()[0])"
	@python -c "import importlib.util as iu; print('✓ Basic video trimmer available' if iu.find_spec('video_trimmer_basic') else '✗ Basic video trimmer not available')"
	@python -c "import importlib.util as iu; print('✓ Advanced video trimmer available' if iu.find_spec('video_trimmer') else '✗ Advanced video trimmer not available')"
	@python -c "import importlib.util as iu; print('✓ FFmpeg trimmer available' if iu.find_spec('ffmpeg_trimmer') else '✗ FFmpeg trimmer not available')"

# Show system info
system-info:
	@echo "System Information:"
	@echo "==================="
	@python -c "import platform; print('OS:', platform.system(), platform.release())"
	@python -c "import platform; print('Python:', platform.python_version())"
	@python -c "import psutil; print('CPU cores:', psutil.cpu_count())"
	@python -c "import psutil; print('RAM:', psutil.virtual_memory().total // (1024**3), 'GB')"
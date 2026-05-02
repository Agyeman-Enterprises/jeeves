@echo off
:: Jeeves — BYOV Wake Word Trainer
:: Double-click or run from any terminal.
:: Uses system Python (no venv needed).

cd /d "%~dp0"
echo.
echo  Jeeves — BYOV Wake Word Trainer
echo  =================================
echo.
python -m app.services.wake_word_byov.train_cli --agent-id jeeves %*
